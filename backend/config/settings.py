"""
Configuration settings for the AI Cheatsheet Pipeline.
All 6 steps with their API keys and model fallback chains.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Base configuration"""

    # ── API Keys ──
    GEMINI_PRO_API_KEY    = os.getenv("GEMINI_PRO_API_KEY", "")     # Step 1, 4, 5
    GEMINI_NANO_API_KEY   = os.getenv("GEMINI_NANO_API_KEY", "")    # Step 2
    DEEP_RESEARCH_API_KEY = os.getenv("DEEP_RESEARCH_API_KEY", "")  # Step 3
    IMAGEN_API_KEY        = os.getenv("IMAGEN_API_KEY", "")         # Step 6

    # ── Pipeline Settings ──
    PIPELINE_MODE   = os.getenv("PIPELINE_MODE", "development")
    MAX_IMAGE_SIZE  = int(os.getenv("MAX_IMAGE_SIZE", "4096"))
    OUTPUT_FORMAT   = os.getenv("OUTPUT_FORMAT", "png")
    TEMPERATURE     = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P           = float(os.getenv("TOP_P", "0.9"))
    MAX_OUTPUT_TOKENS = 8192

    # ── Model Fallback Chains (ordered by free-tier quota: highest first) ──
    # Step 1, 4, 5: Gemini Pro (text understanding + prompt building + content gen)
    GEMINI_PRO_MODELS = [
        "gemini-2.0-flash",       # 1500 RPD — highest quota
        "gemini-2.0-flash-lite",  # Nano Banana — different quota pool
        "gemini-2.5-flash-lite",  # high quota
        "gemini-2.5-flash",       # 500 RPD
        "gemini-2.5-pro",         # 25 RPD — lowest, last resort
    ]
    # Step 2: Nano Banana (image analysis)
    GEMINI_NANO_MODELS = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
    ]
    # Step 3: Deep Research (trend + style analysis)
    DEEP_RESEARCH_MODELS = [
        "gemini-2.0-flash",       # highest quota
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    ]
    # Step 6: Image generation (actual available models from your API key)
    IMAGEN_MODELS = [
        "gemini-2.5-flash-image",           # Available!
        "gemini-3.1-flash-image-preview",   # Available!
        "gemini-3-pro-image-preview",       # Available!
    ]

    # ── Retry / Rate Limit ──
    MAX_RETRIES       = 3
    RETRY_BASE_DELAY  = 2
    RATE_LIMIT_DELAY  = 2      # seconds between pipeline steps

    # ── Timeouts (seconds) ──
    TEXT_GENERATION_TIMEOUT  = 120
    IMAGE_GENERATION_TIMEOUT = 180   # Imagen needs more time
    IMAGE_ANALYSIS_TIMEOUT   = 120

    # ── Directories ──
    BASE_DIR   = Path(__file__).parent.parent
    OUTPUT_DIR = BASE_DIR / "outputs"
    UPLOAD_DIR = BASE_DIR / "uploads"
    LOGS_DIR   = BASE_DIR / "logs"
    TEMP_DIR   = BASE_DIR / "temp"

    @classmethod
    def validate_api_keys(cls) -> bool:
        return bool(cls.GEMINI_PRO_API_KEY and cls.GEMINI_NANO_API_KEY)

    @classmethod
    def validate_all_keys(cls) -> bool:
        return bool(
            cls.GEMINI_PRO_API_KEY
            and cls.GEMINI_NANO_API_KEY
            and cls.DEEP_RESEARCH_API_KEY
            and cls.IMAGEN_API_KEY
        )

    @classmethod
    def print_status(cls):
        keys = {
            "GEMINI_PRO_API_KEY  (Step 1,4,5)": cls.GEMINI_PRO_API_KEY,
            "GEMINI_NANO_API_KEY (Step 2)":      cls.GEMINI_NANO_API_KEY,
            "DEEP_RESEARCH_API_KEY (Step 3)":    cls.DEEP_RESEARCH_API_KEY,
            "IMAGEN_API_KEY (Step 6)":           cls.IMAGEN_API_KEY,
        }
        print("\n🔑 API Key Status:")
        for name, value in keys.items():
            status = "✅ Set" if value else "❌ Missing"
            masked = f"{value[:10]}...{value[-4:]}" if value and len(value) > 14 else value
            print(f"   {name}: {status} ({masked})")
        print(f"\n📦 SDK: google-genai")
        print(f"🤖 Step 1,4,5: {' → '.join(cls.GEMINI_PRO_MODELS)}")
        print(f"🤖 Step 2:     {' → '.join(cls.GEMINI_NANO_MODELS)}")
        print(f"🤖 Step 3:     {' → '.join(cls.DEEP_RESEARCH_MODELS)}")
        print(f"🤖 Step 6:     {' → '.join(cls.IMAGEN_MODELS)}")
        print()


class DevelopmentConfig(Config):
    DEBUG = True
    PIPELINE_MODE = "development"

class ProductionConfig(Config):
    DEBUG = False
    PIPELINE_MODE = "production"

def get_config() -> Config:
    mode = os.getenv("PIPELINE_MODE", "development")
    if mode == "production":
        return ProductionConfig()
    return DevelopmentConfig()

config = get_config()
