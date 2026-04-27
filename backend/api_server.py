"""
FastAPI Server — API layer for the AI Cheatsheet Pipeline

Endpoints:
    GET  /api/health       → Health check + API key status
    POST /api/generate     → Generate cheatsheet (text + image, both optional)
    GET  /api/outputs      → List all generated files
    GET  /outputs/{file}   → Serve generated output files
"""
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Ensure backend is in path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config.settings import config
from src.ai_pipeline.orchestrator import CheatsheetPipeline, CheatsheetPipelineError
from src.utils.logger import pipeline_logger

# ══════════════════════════════════════════════════════════════════
#  App Setup
# ══════════════════════════════════════════════════════════════════
app = FastAPI(
    title="AI Cheatsheet Pipeline API",
    description="6-Step AI-powered cheatsheet generation pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
#  Health Check
# ══════════════════════════════════════════════════════════════════
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "pipeline": "AI Cheatsheet Generator",
        "version": "1.0.0",
        "api_keys_configured": {
            "gemini_pro": bool(config.GEMINI_PRO_API_KEY),
            "gemini_nano": bool(config.GEMINI_NANO_API_KEY),
            "deep_research": bool(config.DEEP_RESEARCH_API_KEY),
            "imagen": bool(config.IMAGEN_API_KEY),
        },
    }


@app.get("/api/test")
async def test_endpoint():
    """Simple test to verify the server is alive"""
    return {"ok": True, "message": "Backend is running!"}


# ══════════════════════════════════════════════════════════════════
#  UNIFIED Generate Endpoint
# ══════════════════════════════════════════════════════════════════
@app.post("/api/generate")
async def generate_cheatsheet(
    prompt: str = Form(""),
    image: UploadFile = File(None),
):
    """
    Generate a cheatsheet from text prompt AND/OR uploaded image.
    """
    try:
        # Normalize inputs
        prompt_text = (prompt or "").strip()
        has_prompt = len(prompt_text) >= 2
        has_image = (
            image is not None
            and hasattr(image, 'filename')
            and image.filename
            and len(image.filename) > 0
        )

        if not has_prompt and not has_image:
            return JSONResponse(
                status_code=400,
                content={"detail": "Please provide a text prompt, an image, or both"}
            )

        if not config.GEMINI_PRO_API_KEY:
            return JSONResponse(
                status_code=503,
                content={"detail": "API keys not configured. Set GEMINI_PRO_API_KEY in .env"}
            )

        # Save uploaded image if provided
        image_path = None
        if has_image:
            timestamp_img = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = Path(image.filename).suffix or ".png"
            upload_path = config.UPLOAD_DIR / f"upload_{timestamp_img}{ext}"
            upload_path.parent.mkdir(parents=True, exist_ok=True)

            file_bytes = await image.read()
            with open(upload_path, "wb") as f:
                f.write(file_bytes)
            image_path = str(upload_path)
            print(f"   📸 Image saved: {upload_path} ({len(file_bytes)} bytes)")

        mode_desc = "text+image" if (has_prompt and has_image) else ("image" if has_image else "text")
        print(f"\n{'='*60}")
        print(f"   🚀 API Generate ({mode_desc}): '{prompt_text[:60]}'")
        print(f"{'='*60}")

        pipeline = CheatsheetPipeline()
        
        # If image-only (no text prompt), auto-generate a basic prompt
        # so the pipeline always has something to work with even if image analysis fails
        effective_prompt = prompt_text if has_prompt else ""
        if has_image and not has_prompt:
            effective_prompt = "Create a comprehensive technology cheatsheet based on the uploaded image. Include all key concepts, tips, and best practices."
        
        result = await pipeline.generate_combined(
            user_prompt=effective_prompt,
            image_path=image_path,
            output_format="html",
            generate_image=True,
        )

        # Build response
        response = {
            "status": "success",
            "title": result.get("title", ""),
            "mode": result.get("mode", mode_desc),
            "generation_time": result.get("generation_time", ""),
        }

        text_path = result.get("text_output", "")
        if text_path:
            filename = Path(text_path).name
            response["text_output"] = f"/outputs/{filename}"
            response["text_filename"] = filename

        img_output = result.get("image_output")
        if img_output:
            filename = Path(img_output).name
            response["image_output"] = f"/outputs/{filename}"
            response["image_filename"] = filename

        ua = result.get("user_analysis", {})
        response["analysis"] = {
            "topic": ua.get("topic", ""),
            "subtopics": ua.get("subtopics", []),
            "difficulty": ua.get("difficulty", ""),
        }

        print(f"\n   ✅ API Success: {response.get('title', 'N/A')}")
        return response

    except CheatsheetPipelineError as e:
        print(f"\n   ❌ Pipeline error: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})
    except Exception as e:
        tb = traceback.format_exc()
        print(f"\n   ❌ Unexpected error: {e}\n{tb}")
        return JSONResponse(status_code=500, content={"detail": f"Pipeline failed: {str(e)}"})


# ══════════════════════════════════════════════════════════════════
#  List Generated Outputs
# ══════════════════════════════════════════════════════════════════
@app.get("/api/outputs")
async def list_outputs():
    files = []
    for f in sorted(config.OUTPUT_DIR.iterdir(), reverse=True):
        if f.is_file():
            files.append({
                "filename": f.name,
                "url": f"/outputs/{f.name}",
                "size": f.stat().st_size,
                "type": f.suffix.lstrip("."),
            })
    return {"outputs": files, "count": len(files)}


# ══════════════════════════════════════════════════════════════════
#  Static Files — MUST be last (greedy mount)
# ══════════════════════════════════════════════════════════════════
app.mount("/outputs", StaticFiles(directory=str(config.OUTPUT_DIR)), name="outputs")


# ══════════════════════════════════════════════════════════════════
#  Run Server
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting AI Cheatsheet Pipeline API Server...")
    print(f"   http://localhost:8000")
    print(f"   Docs:  http://localhost:8000/docs")
    print(f"   Test:  http://localhost:8000/api/test\n")
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src", "config"],
        timeout_keep_alive=600,
    )


