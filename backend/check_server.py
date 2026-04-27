"""
Quick diagnostic — run this to check if the backend can start.
Usage: python check_server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 50)
print("  Backend Server Diagnostic")
print("=" * 50)

# 1. Check Python
print(f"\n[1] Python: {sys.version}")

# 2. Check FastAPI
try:
    import fastapi
    print(f"[2] FastAPI: {fastapi.__version__} ✅")
except ImportError:
    print("[2] FastAPI: NOT INSTALLED ❌")
    print("    Fix: pip install fastapi uvicorn python-multipart")
    sys.exit(1)

# 3. Check uvicorn
try:
    import uvicorn
    print(f"[3] Uvicorn: installed ✅")
except ImportError:
    print("[3] Uvicorn: NOT INSTALLED ❌")
    print("    Fix: pip install uvicorn")
    sys.exit(1)

# 4. Check python-multipart (needed for Form/File uploads)
try:
    import multipart
    print(f"[4] python-multipart: installed ✅")
except ImportError:
    try:
        from multipart.multipart import parse_options_header
        print(f"[4] python-multipart: installed ✅")
    except ImportError:
        print("[4] python-multipart: NOT INSTALLED ❌")
        print("    Fix: pip install python-multipart")
        sys.exit(1)

# 5. Check config imports
try:
    from config.settings import config
    print(f"[5] Config: loaded ✅")
    print(f"    API Key set: {bool(config.GEMINI_PRO_API_KEY)}")
    print(f"    Output dir: {config.OUTPUT_DIR}")
    print(f"    Upload dir: {config.UPLOAD_DIR}")
except Exception as e:
    print(f"[5] Config: FAILED ❌ — {e}")
    sys.exit(1)

# 6. Check orchestrator import
try:
    from src.ai_pipeline.orchestrator import CheatsheetPipeline
    print(f"[6] Orchestrator: imported ✅")
except Exception as e:
    print(f"[6] Orchestrator: FAILED ❌ — {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 7. Check api_server import
try:
    from api_server import app
    print(f"[7] API Server: imported ✅")
except Exception as e:
    print(f"[7] API Server: FAILED ❌ — {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n{'=' * 50}")
print(f"  ALL CHECKS PASSED ✅")
print(f"  Run: python api_server.py")
print(f"{'=' * 50}")
