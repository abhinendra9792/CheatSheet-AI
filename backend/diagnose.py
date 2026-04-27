"""
Quick API Key Diagnostic — Tests each key individually
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Try importing google-genai
try:
    from google import genai
    from google.genai import types
    print("✅ google-genai SDK installed")
except ImportError:
    print("❌ google-genai not installed. Run: pip install google-genai")
    sys.exit(1)

print("\n" + "=" * 60)
print("🔍 API KEY DIAGNOSTIC")
print("=" * 60)

keys = {
    "GEMINI_PRO_API_KEY (Step 1,4,5)": os.getenv("GEMINI_PRO_API_KEY", ""),
    "GEMINI_NANO_API_KEY (Step 2)": os.getenv("GEMINI_NANO_API_KEY", ""),
    "DEEP_RESEARCH_API_KEY (Step 3)": os.getenv("DEEP_RESEARCH_API_KEY", ""),
    "IMAGEN_API_KEY (Step 6)": os.getenv("IMAGEN_API_KEY", ""),
}

# Show keys
for name, key in keys.items():
    if key:
        print(f"  {name}: {key[:12]}...{key[-4:]}")
    else:
        print(f"  {name}: ❌ NOT SET")

# Test each key with a minimal API call
print("\n" + "=" * 60)
print("🧪 TESTING EACH KEY WITH MINIMAL API CALL")
print("=" * 60)

test_models = [
    ("gemini-2.0-flash", "GEMINI_PRO_API_KEY"),
    ("gemini-2.5-flash", "GEMINI_PRO_API_KEY"),
    ("gemini-2.0-flash-lite", "GEMINI_NANO_API_KEY"),
]

for model, key_name in test_models:
    api_key = os.getenv(key_name, "")
    if not api_key:
        print(f"\n  ⏭️  Skipping {model} — {key_name} not set")
        continue

    print(f"\n  Testing {model} with {key_name}...")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents="Say hello in exactly 3 words.",
            config=types.GenerateContentConfig(
                max_output_tokens=20,
            ),
        )
        print(f"  ✅ {model}: SUCCESS — Response: '{response.text.strip()}'")
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            print(f"  ⚠️ {model}: RATE LIMITED (429) — Key works but quota exhausted")
        elif "403" in err:
            print(f"  ❌ {model}: FORBIDDEN (403) — API not enabled for this key")
        elif "400" in err:
            print(f"  ❌ {model}: BAD REQUEST (400) — {err[:100]}")
        elif "404" in err:
            print(f"  ❌ {model}: NOT FOUND (404) — Model not available")
        else:
            print(f"  ❌ {model}: ERROR — {err[:150]}")

# Test image generation model
print(f"\n  Testing gemini-2.0-flash-preview-image-generation...")
try:
    api_key = os.getenv("GEMINI_PRO_API_KEY", "")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents="Generate a simple blue square",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    has_image = False
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                has_image = True
                print(f"  ✅ Image gen: SUCCESS — Got image bytes ({len(part.inline_data.data)} bytes)")
    if not has_image:
        print(f"  ⚠️ Image gen: No image in response")
except Exception as e:
    err = str(e)
    if "429" in err:
        print(f"  ⚠️ Image gen: RATE LIMITED — Key works but quota exhausted")
    else:
        print(f"  ❌ Image gen: ERROR — {err[:150]}")

# List available models
print("\n" + "=" * 60)
print("📋 LISTING AVAILABLE MODELS FOR YOUR KEY")
print("=" * 60)
try:
    api_key = os.getenv("GEMINI_PRO_API_KEY", "")
    client = genai.Client(api_key=api_key)
    models = client.models.list()
    print("  Available Gemini models:")
    for m in models:
        if "gemini" in m.name.lower() or "imagen" in m.name.lower():
            print(f"    • {m.name}")
except Exception as e:
    print(f"  ❌ Could not list models: {str(e)[:100]}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
