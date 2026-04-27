#!/usr/bin/env python3
"""
Main entry point for AI Cheatsheet Generation Pipeline

Full 6-Step Pipeline:
  Step 1: Understand User      → Gemini Pro
  Step 2: Analyze Old Image    → Nano Banana Pro
  Step 3: Trend + Style        → Deep Research Pro
  Step 4: Build Final Prompt   → Gemini Pro
  Step 5: Generate Content     → Gemini Pro
  Step 6: Generate Image       → Imagen 4 Ultra

Usage:
    python main.py --prompt "Your topic"
    python main.py --image path/to/image.png
    python main.py --prompt "Topic" --no-image
    python main.py --check
"""
import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.ai_pipeline.orchestrator import CheatsheetPipeline
from config.settings import config
from src.utils.logger import pipeline_logger


def print_banner():
    print("""
╔════════════════════════════════════════════════════════════════╗
║          AI CHEATSHEET GENERATION PIPELINE                    ║
║                                                               ║
║  Step 1: Gemini Pro         →  Understand User                ║
║  Step 2: Nano Banana Pro    →  Analyze Old Image              ║
║  Step 3: Deep Research Pro  →  Trend + Style Upgrade          ║
║  Step 4: Gemini Pro         →  Build Final Prompt             ║
║  Step 5: Gemini Pro         →  Generate Content               ║
║  Step 6: Imagen 4 Ultra     →  Generate Cheatsheet Image 🎯  ║
╚════════════════════════════════════════════════════════════════╝
    """)


async def main():
    parser = argparse.ArgumentParser(
        description="AI Cheatsheet Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --check
  python main.py --prompt "REST API design principles"
  python main.py --prompt "Python basics" --no-image
  python main.py --image cheatsheet.png
  python main.py --prompt "ML" --title "Machine Learning 101"
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", type=str, help="Text prompt for cheatsheet")
    group.add_argument("--image",  type=str, help="Path to image to analyze")
    group.add_argument("--check",  action="store_true", help="Check API keys")

    parser.add_argument("--title", type=str, default=None, help="Custom title")
    parser.add_argument("--no-image", action="store_true",
                        help="Skip Step 6 (image generation)")
    parser.add_argument("--format", choices=["txt", "html"],
                        default="txt", help="Output format (default: txt)")

    args = parser.parse_args()
    print_banner()

    # ── Check mode ───────────────────────────────────────────────
    if args.check:
        config.print_status()
        if config.validate_all_keys():
            print("✅ All 6 API keys configured. Full pipeline ready!\n")
        elif config.validate_api_keys():
            print("⚠️  Core keys OK, but some optional keys missing.\n")
        else:
            print("❌ Missing required API keys. Update backend/.env\n")
            sys.exit(1)
        sys.exit(0)

    # ── Validate ─────────────────────────────────────────────────
    if not config.validate_api_keys():
        print("❌ API keys not configured! Run: python main.py --check")
        sys.exit(1)

    generate_image = not args.no_image

    # ── Text mode ────────────────────────────────────────────────
    if args.prompt:
        print(f"📝 Mode: Text → Cheatsheet")
        print(f"   Prompt:  {args.prompt}")
        print(f"   Image:   {'Yes (Step 6)' if generate_image else 'Skipped'}")
        print(f"   Format:  {args.format}\n")

        try:
            pipeline = CheatsheetPipeline()
            result = await pipeline.generate_from_text_prompt(
                user_prompt=args.prompt,
                cheatsheet_title=args.title,
                output_format=args.format,
                generate_image=generate_image,
            )
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            pipeline_logger.error(f"Pipeline failed: {e}", exc_info=True)
            sys.exit(1)

    # ── Image mode ───────────────────────────────────────────────
    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"❌ Image file not found: {args.image}")
            sys.exit(1)

        print(f"📸 Mode: Image → Cheatsheet")
        print(f"   Image:   {args.image}")
        print(f"   Image:   {'Yes (Step 6)' if generate_image else 'Skipped'}")
        print(f"   Format:  {args.format}\n")

        try:
            pipeline = CheatsheetPipeline()
            result = await pipeline.generate_from_image(
                image_path=str(image_path),
                output_format=args.format,
                generate_image=generate_image,
            )
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            pipeline_logger.error(f"Image pipeline failed: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
