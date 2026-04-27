"""
Image Analyzer Module — Step 2: Analyze Old Image (Optional)
Uses Nano Banana Pro via the NEW google-genai SDK with model fallback.

Model fallback chain: gemini-2.0-flash-lite → gemini-2.0-flash
"""
import asyncio
import json
from typing import Dict, Optional, Any
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
from src.utils.logger import image_analysis_logger
from config.settings import config


class ImageAnalysisError(Exception):
    """Exception raised for image analysis errors"""
    pass


class ImageAnalyzer:
    """
    Step 2: Analyze uploaded cheatsheet/reference images.
    Has smart model fallback to handle rate limits.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ImageAnalyzer with Nano Banana Pro API key (Step 2).
        """
        self.api_key = api_key or config.GEMINI_NANO_API_KEY
        self.logger = image_analysis_logger
        self.model_chain = config.GEMINI_NANO_MODELS  # Fallback chain
        self.max_image_size = config.MAX_IMAGE_SIZE

        if not self.api_key:
            raise ImageAnalysisError(
                "GEMINI_NANO_API_KEY not configured. "
                "Set it in backend/.env (Step 2 key)."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.logger.info(
            f"ImageAnalyzer initialized | models={self.model_chain} | SDK=google-genai"
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Image preparation
    # ──────────────────────────────────────────────────────────────────────
    def _prepare_image(self, image_path: str) -> Image.Image:
        """Load, validate, resize and convert image to RGB."""
        path = Path(image_path)
        if not path.exists():
            raise ImageAnalysisError(f"Image file not found: {image_path}")

        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}:
            raise ImageAnalysisError(
                f"Unsupported image format: {path.suffix}. "
                "Supported: PNG, JPG, JPEG, GIF, WEBP, BMP"
            )

        try:
            image = Image.open(image_path)

            if max(image.size) > self.max_image_size:
                self.logger.info(f"Resizing {image.size} → max {self.max_image_size}")
                image.thumbnail(
                    (self.max_image_size, self.max_image_size),
                    Image.Resampling.LANCZOS,
                )

            if image.mode == "RGBA":
                bg = Image.new("RGB", image.size, (255, 255, 255))
                bg.paste(image, mask=image.split()[3])
                image = bg
            elif image.mode != "RGB":
                image = image.convert("RGB")

            self.logger.info(f"Image prepared: {image.size}, mode={image.mode}")
            return image

        except ImageAnalysisError:
            raise
        except Exception as e:
            raise ImageAnalysisError(f"Failed to prepare image: {e}")

    # ──────────────────────────────────────────────────────────────────────
    #  Core: _call_model with fallback chain
    # ──────────────────────────────────────────────────────────────────────
    async def _call_model(
        self,
        contents: list,
        timeout: int = None,
    ) -> str:
        """
        Call the Gemini API with model fallback chain.
        Tries each model; if one hits 429, moves to next.
        """
        timeout = timeout or config.IMAGE_ANALYSIS_TIMEOUT
        errors = []

        for model_name in self.model_chain:
            try:
                self.logger.info(f"Trying model={model_name}")

                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda m=model_name: self.client.models.generate_content(
                            model=m,
                            contents=contents,
                        ),
                    ),
                    timeout=timeout,
                )

                self.logger.info(f"✅ Response from {model_name}")
                return response.text

            except asyncio.TimeoutError:
                msg = f"{model_name}: timed out after {timeout}s"
                self.logger.warning(msg)
                errors.append(msg)
                continue

            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str

                if is_rate_limit:
                    self.logger.warning(
                        f"⚠️ {model_name}: Rate limited. Trying next model..."
                    )
                    errors.append(f"{model_name}: Rate limited")
                    await asyncio.sleep(2)
                    continue
                else:
                    msg = f"{model_name}: {error_str}"
                    self.logger.warning(msg)
                    errors.append(msg)
                    continue

        all_errors = " | ".join(errors)
        raise ImageAnalysisError(f"All models failed. Errors: {all_errors}")

    # ──────────────────────────────────────────────────────────────────────
    #  Step 2: Analyze Old Image — main method
    # ──────────────────────────────────────────────────────────────────────
    async def analyze_image(
        self,
        image_path: str,
        timeout: int = None,
    ) -> Dict[str, Any]:
        """
        Step 2 — Analyze Old Image: Extract comprehensive information from
        an uploaded cheatsheet image.
        """
        try:
            self.logger.info(f"[Step 2] Analyzing image: {image_path}")
            image = self._prepare_image(image_path)

            prompt = """You are an expert cheatsheet analyst. Analyze this cheatsheet/reference image thoroughly.

Extract ALL information and provide your analysis as JSON with these exact keys:
{
    "topic": "The main topic of this cheatsheet",
    "subtopics": ["list", "of", "all", "subtopics", "covered"],
    "extracted_text": "ALL readable text from the image, preserving structure",
    "structure": {
        "sections": ["list of section titles/headings found"],
        "hierarchy": "Description of how information is organized",
        "num_sections": 0
    },
    "design_elements": {
        "layout": "Description of layout (grid, columns, flow, etc.)",
        "colors": ["list of dominant colors used"],
        "typography": "Font style observations",
        "icons_graphics": "Description of any icons or graphics"
    },
    "color_scheme": {
        "primary": "Primary color",
        "secondary": "Secondary color",
        "accent": "Accent color",
        "background": "Background color"
    },
    "key_concepts": ["list", "of", "core", "concepts", "explained"],
    "difficulty": "beginner | intermediate | advanced",
    "suggested_improvements": ["list", "of", "ways", "to", "improve"]
}

Respond with ONLY valid JSON, no markdown formatting or code blocks."""

            response_text = await self._call_model(
                contents=[prompt, image],
                timeout=timeout,
            )

            result = self._parse_json_response(response_text)
            self.logger.info(
                f"[Step 2] ✅ Analysis complete — topic: {result.get('topic', 'unknown')}"
            )
            return result

        except ImageAnalysisError:
            raise
        except Exception as e:
            msg = f"Image analysis failed: {e}"
            self.logger.error(msg)
            raise ImageAnalysisError(msg)

    # ──────────────────────────────────────────────────────────────────────
    #  Quick text extraction
    # ──────────────────────────────────────────────────────────────────────
    async def extract_text(self, image_path: str, timeout: int = None) -> str:
        """Extract all visible text from an image (OCR-like)."""
        try:
            self.logger.info(f"Extracting text from: {image_path}")
            image = self._prepare_image(image_path)

            prompt = (
                "Extract and transcribe ALL text visible in this image. "
                "Preserve the original structure and formatting as much as possible. "
                "Include headings, bullet points, code snippets, and notes."
            )

            return await self._call_model(
                contents=[prompt, image],
                timeout=timeout,
            )

        except Exception as e:
            msg = f"Text extraction failed: {e}"
            self.logger.error(msg)
            raise ImageAnalysisError(msg)

    # ──────────────────────────────────────────────────────────────────────
    #  JSON parsing helper
    # ──────────────────────────────────────────────────────────────────────
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from the model's response text."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        start = cleaned.find("{")
        if start == -1:
            return {"raw_response": text}

        brace_count = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                brace_count += 1
            elif cleaned[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    try:
                        return json.loads(cleaned[start : i + 1])
                    except json.JSONDecodeError:
                        return {"raw_response": text}

        return {"raw_response": text}
