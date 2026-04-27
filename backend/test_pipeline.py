#!/usr/bin/env python3
"""
AI Cheatsheet Pipeline — Terminal Test Suite

Tests each step individually and the full 6-step pipeline:
  --text  "topic"     → Test Step 1 (Understand User)
  --image path.png    → Test Step 2 (Analyze Image)
  --step3 "topic"     → Test Step 3 (Trend Research)
  --step6 "topic"     → Test Step 6 (Image Generation)
  --full  "topic"     → Full pipeline (Steps 1→3→4→5→6)
  --full-image p.png  → Full pipeline from image (Steps 2→1→3→4→5→6)
"""
import asyncio
import argparse
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import config


def print_banner():
    print("""
╔════════════════════════════════════════════════════════════════╗
║          AI CHEATSHEET PIPELINE — TERMINAL TESTER             ║
║  Step 1: Gemini Pro   |  Step 2: Nano Banana Pro              ║
║  Step 3: Deep Research|  Step 4: Prompt Builder                ║
║  Step 5: Gemini Pro   |  Step 6: Imagen 4 Ultra               ║
╚════════════════════════════════════════════════════════════════╝
    """)


def print_keys():
    print("\n🔑 Checking API Key Configuration...\n")
    config.print_status()
    if config.validate_api_keys():
        print("✅ Core API keys (Step 1 + Step 2) are configured!")
    else:
        print("❌ Missing required API keys. Update backend/.env")
        sys.exit(1)
    if config.validate_all_keys():
        print("✅ All 6-step keys are configured!\n")
    else:
        print("⚠️  Some optional keys missing (Step 3/6 may fail)\n")


def print_json(data, indent=2, max_depth=2):
    """Pretty print JSON with depth limit"""
    def truncate(obj, depth=0):
        if depth >= max_depth:
            if isinstance(obj, dict):
                return f"{{...{len(obj)} keys}}"
            if isinstance(obj, list):
                return f"[...{len(obj)} items]"
            if isinstance(obj, str) and len(obj) > 200:
                return obj[:200] + "..."
            return obj
        if isinstance(obj, dict):
            return {k: truncate(v, depth + 1) for k, v in obj.items()}
        if isinstance(obj, list):
            return [truncate(v, depth + 1) for v in obj[:5]]
        if isinstance(obj, str) and len(obj) > 300:
            return obj[:300] + "..."
        return obj

    print(json.dumps(truncate(data), indent=indent, ensure_ascii=False))


# ══════════════════════════════════════════════════════════════════
#  Individual Step Tests
# ══════════════════════════════════════════════════════════════════

async def test_step1_text(prompt: str) -> dict:
    """Test Step 1: Understand User (Gemini Pro)"""
    print("=" * 60)
    print("🧠 TESTING STEP 1: Understand User (Gemini Pro)")
    print("=" * 60)
    print(f"   Prompt: {prompt}\n")

    from src.modules.text_generator import TextGenerator
    tg = TextGenerator()
    result = await tg.understand_user_input(prompt)

    print("\n📋 Result:")
    print_json(result)
    return result


async def test_step2_image(image_path: str) -> dict:
    """Test Step 2: Analyze Image (Nano Banana Pro)"""
    print("=" * 60)
    print("📸 TESTING STEP 2: Analyze Old Image (Nano Banana Pro)")
    print("=" * 60)
    print(f"   Image: {image_path}\n")

    if not Path(image_path).exists():
        print(f"   ❌ Image file not found: {image_path}")
        return {}

    from src.modules.image_analyzer import ImageAnalyzer
    ia = ImageAnalyzer()
    result = await ia.analyze_image(image_path)

    print("\n📋 Result:")
    print_json(result)
    return result


async def test_step3_trends(prompt: str) -> dict:
    """Test Step 3: Trend + Style Research (Deep Research Pro)"""
    print("=" * 60)
    print("🔍 TESTING STEP 3: Trend + Style Upgrade (Deep Research)")
    print("=" * 60)
    print(f"   Topic: {prompt}\n")

    # First run Step 1 to get analysis
    from src.modules.text_generator import TextGenerator
    tg = TextGenerator()
    print("   Running Step 1 first to get analysis...")
    analysis = await tg.understand_user_input(prompt)
    print(f"   ✅ Step 1 done: topic={analysis.get('topic', 'N/A')}\n")

    await asyncio.sleep(3)

    from src.modules.trend_researcher import TrendResearcher
    tr = TrendResearcher()
    result = await tr.research_trends(analysis)

    print("\n📋 Trend Result:")
    print_json(result)
    return result


async def test_step6_image(prompt: str) -> str:
    """Test Step 6: Generate Image (Imagen 4 Ultra)"""
    print("=" * 60)
    print("🎨 TESTING STEP 6: Generate Cheatsheet Image (Imagen 4 Ultra)")
    print("=" * 60)
    print(f"   Topic: {prompt}\n")

    # Run Steps 1 → 3 to build required data
    from src.modules.text_generator import TextGenerator
    from src.modules.trend_researcher import TrendResearcher
    from src.modules.image_generator import ImageGenerator

    tg = TextGenerator()
    print("   Running Step 1...")
    analysis = await tg.understand_user_input(prompt)
    print(f"   ✅ Step 1 done")

    await asyncio.sleep(3)

    try:
        tr = TrendResearcher()
        print("   Running Step 3...")
        trend_data = await tr.research_trends(analysis)
        print(f"   ✅ Step 3 done")
    except Exception as e:
        print(f"   ⚠️ Step 3 failed (using defaults): {e}")
        trend_data = {
            "design_style": {"theme": "Modern dark", "mood": "Professional"},
            "color_palette": {"primary": "#2563EB", "background": "#0F172A", "text": "#F8FAFC", "palette_name": "Tech Blue"},
            "layout_recommendation": {"type": "grid", "sections": 6, "description": "Grid layout"},
            "visual_elements": ["headers", "bullet points"],
            "typography": {"title_font": "sans-serif bold", "body_font": "sans-serif"},
            "imagen_prompt_hints": f"Professional cheatsheet about {analysis.get('topic', prompt)}",
        }

    await asyncio.sleep(3)

    ig = ImageGenerator()
    title = analysis.get("suggested_title", prompt[:40])
    content_summary = f"Topic: {analysis.get('topic')}\nSubtopics: {', '.join(analysis.get('subtopics', []))}"

    print(f"\n   Generating image for: {title}")
    image_path = await ig.generate_cheatsheet_image(
        title=title,
        content_summary=content_summary,
        trend_data=trend_data,
    )

    print(f"\n   ✅ Image saved: {image_path}")
    return image_path


# ══════════════════════════════════════════════════════════════════
#  Full Pipeline Tests
# ══════════════════════════════════════════════════════════════════

async def test_full_text_pipeline(prompt: str) -> dict:
    """Full pipeline: Steps 1 → 3 → 4 → 5 → 6"""
    print("=" * 60)
    print("🚀 FULL TEXT PIPELINE (Steps 1 → 3 → 4 → 5 → 6)")
    print("=" * 60)
    print(f"   Prompt: {prompt}\n")

    from src.ai_pipeline.orchestrator import CheatsheetPipeline
    pipeline = CheatsheetPipeline()
    result = await pipeline.generate_from_text_prompt(
        user_prompt=prompt,
        output_format="txt",
        generate_image=True,
    )
    return result


async def test_full_image_pipeline(image_path: str) -> dict:
    """Full pipeline: Steps 2 → 1 → 3 → 4 → 5 → 6"""
    print("=" * 60)
    print("🚀 FULL IMAGE PIPELINE (Steps 2 → 1 → 3 → 4 → 5 → 6)")
    print("=" * 60)
    print(f"   Image: {image_path}\n")

    if not Path(image_path).exists():
        print(f"   ❌ Image file not found: {image_path}")
        return {}

    from src.ai_pipeline.orchestrator import CheatsheetPipeline
    pipeline = CheatsheetPipeline()
    result = await pipeline.generate_from_image(
        image_path=image_path,
        output_format="txt",
        generate_image=True,
    )
    return result


# ══════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="AI Cheatsheet Pipeline — Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_pipeline.py --text "Python data structures"
  python test_pipeline.py --image cheatsheet.png
  python test_pipeline.py --step3 "Machine Learning"
  python test_pipeline.py --step6 "REST API design"
  python test_pipeline.py --full "Cloud Computing"
  python test_pipeline.py --full-image cheatsheet.png
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text",       type=str, help="Test Step 1: Text understanding")
    group.add_argument("--image",      type=str, help="Test Step 2: Image analysis")
    group.add_argument("--step3",      type=str, help="Test Step 3: Trend research")
    group.add_argument("--step6",      type=str, help="Test Step 6: Image generation")
    group.add_argument("--full",       type=str, help="Full text pipeline (1→3→4→5→6)")
    group.add_argument("--full-image", type=str, help="Full image pipeline (2→1→3→4→5→6)")

    args = parser.parse_args()

    print_banner()
    print_keys()

    results = {}

    try:
        if args.text:
            r = await test_step1_text(args.text)
            results["step1_text"] = "✅ PASS" if r.get("topic") else "❌ FAIL"

        elif args.image:
            r = await test_step2_image(args.image)
            results["step2_image"] = "✅ PASS" if r.get("topic") else "❌ FAIL"

        elif args.step3:
            r = await test_step3_trends(args.step3)
            results["step3_trends"] = "✅ PASS" if r.get("latest_trends") else "❌ FAIL"

        elif args.step6:
            r = await test_step6_image(args.step6)
            results["step6_image"] = "✅ PASS" if r else "❌ FAIL"

        elif args.full:
            r = await test_full_text_pipeline(args.full)
            results["full_text_pipeline"] = "✅ PASS" if r.get("status") == "success" else "❌ FAIL"

        elif args.full_image:
            r = await test_full_image_pipeline(args.full_image)
            results["full_image_pipeline"] = "✅ PASS" if r.get("status") == "success" else "❌ FAIL"

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        test_name = list(results.keys())[0] if results else "test"
        results[test_name] = "❌ FAIL"

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    for name, status in results.items():
        print(f"   {name}: {status}")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Tests cancelled")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
