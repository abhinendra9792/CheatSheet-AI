"""
Image Generator Module — Step 6: Generate Cheatsheet Image 🎯

Strategy:
  1. PRIMARY: Use Gemini 2.0 Flash (free tier!) via generate_content
     with response_modalities=["IMAGE"] — works on free API keys
  2. FALLBACK: Generate a professional HTML cheatsheet and save it

Input:  Content from Step 5 + Style from Step 3 + Final prompt from Step 4
Output: Generated cheatsheet image (PNG) or HTML file
"""
import asyncio
import json
import base64
from typing import Dict, Optional, Any
from pathlib import Path
from io import BytesIO
from datetime import datetime

from google import genai
from google.genai import types
from PIL import Image

from src.utils.logger import image_gen_logger
from config.settings import config


class ImageGenerationError(Exception):
    """Exception raised for image generation errors"""
    pass


class ImageGenerator:
    """
    Step 6: Generate the final cheatsheet as a professional image.

    Primary:  Gemini 2.0 Flash image generation (free tier)
    Fallback: HTML cheatsheet output
    """

    def __init__(self, api_key: Optional[str] = None):
        # Use GEMINI_PRO_API_KEY — we're using Gemini Flash for image gen (free tier!)
        self.api_key = api_key or config.GEMINI_PRO_API_KEY or config.IMAGEN_API_KEY
        self.logger = image_gen_logger

        # Gemini models that support image generation (from your available models)
        self.gemini_image_models = [
            "gemini-2.5-flash-image",          # Verified available
            "gemini-3.1-flash-image-preview",  # Verified available
            "gemini-3-pro-image-preview",      # Verified available
        ]

        if not self.api_key:
            raise ImageGenerationError(
                "No API key configured for image generation. "
                "Set IMAGEN_API_KEY or GEMINI_PRO_API_KEY in .env"
            )

        self.client = genai.Client(api_key=self.api_key)
        self.output_dir = config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            f"ImageGenerator initialized | strategy=gemini-flash-image | SDK=google-genai"
        )

    # ══════════════════════════════════════════════════════════════════
    #  Step 6: Generate Cheatsheet Image
    # ══════════════════════════════════════════════════════════════════
    async def generate_cheatsheet_image(
        self,
        title: str,
        content_summary: str,
        trend_data: Dict[str, Any],
        timeout: int = None,
    ) -> str:
        """
        Step 6 — Generate Cheatsheet Image.

        Tries:
          1. Gemini 2.0 Flash image generation (free tier)
          2. HTML cheatsheet fallback (always works)

        Returns:
            Path to the saved image/HTML file
        """
        timeout = timeout or config.IMAGE_GENERATION_TIMEOUT
        imagen_prompt = self._build_imagen_prompt(title, content_summary, trend_data)

        self.logger.info(f"[Step 6] Generating cheatsheet image for: {title}")

        # ── Try 1: Gemini Flash image generation (free tier) ──────
        for model_name in self.gemini_image_models:
            try:
                self.logger.info(f"Trying Gemini image gen: {model_name}")
                print(f"   Trying: {model_name}...")

                image_config = types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                )

                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda m=model_name: self.client.models.generate_content(
                            model=m,
                            contents=imagen_prompt,
                            config=image_config,
                        ),
                    ),
                    timeout=timeout,
                )

                # Extract image from response
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            image_bytes = part.inline_data.data
                            output_path = self._save_image(title, image_bytes)
                            self.logger.info(f"[Step 6] Image saved: {output_path}")
                            return output_path

                self.logger.warning(f"{model_name}: No image in response")

            except asyncio.TimeoutError:
                self.logger.warning(f"{model_name}: Timed out after {timeout}s")
                continue
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    self.logger.warning(f"{model_name}: Rate limited")
                    print(f"   Rate limited, waiting 15s...")
                    await asyncio.sleep(15)
                    # Retry once after wait
                    try:
                        response = await asyncio.wait_for(
                            loop.run_in_executor(
                                None,
                                lambda m=model_name: self.client.models.generate_content(
                                    model=m,
                                    contents=imagen_prompt,
                                    config=image_config,
                                ),
                            ),
                            timeout=timeout,
                        )
                        if response.candidates:
                            for part in response.candidates[0].content.parts:
                                if part.inline_data:
                                    image_bytes = part.inline_data.data
                                    output_path = self._save_image(title, image_bytes)
                                    return output_path
                    except Exception:
                        pass
                    continue
                self.logger.warning(f"{model_name}: {err[:150]}")
                continue

        # ── Try 2: HTML cheatsheet fallback (always works) ────────
        self.logger.info("[Step 6] Gemini image gen failed, generating HTML cheatsheet")
        print(f"   Generating HTML cheatsheet (fallback)...")
        return self._generate_html_cheatsheet(title, content_summary, trend_data)

    # ══════════════════════════════════════════════════════════════════
    #  Build the image prompt
    # ══════════════════════════════════════════════════════════════════
    def _build_imagen_prompt(
        self, title: str, content_summary: str, trend_data: Dict[str, Any]
    ) -> str:
        design = trend_data.get("design_style", {})
        colors = trend_data.get("color_palette", {})
        layout = trend_data.get("layout_recommendation", {})
        visual_elements = trend_data.get("visual_elements", [])
        imagen_hints = trend_data.get("imagen_prompt_hints", "")

        color_desc = ""
        if colors:
            color_desc = (
                f"Color palette: primary {colors.get('primary', '#2563EB')}, "
                f"accent {colors.get('accent', '#F59E0B')}, "
                f"background {colors.get('background', '#0F172A')}. "
            )

        layout_desc = ""
        if layout:
            layout_desc = (
                f"Layout: {layout.get('type', 'grid')} with "
                f"{layout.get('sections', 6)} sections. "
            )

        visuals_desc = ""
        if visual_elements:
            visuals_desc = f"Elements: {', '.join(visual_elements[:6])}. "

        content_lines = content_summary[:600]

        prompt = (
            f"Create a professional, high-quality cheatsheet infographic titled '{title}'. "
            f"{imagen_hints} "
            f"Theme: {design.get('theme', 'Modern dark')}. "
            f"{color_desc}{layout_desc}{visuals_desc}"
            f"Content: {content_lines}. "
            f"Style: Clean infographic with clear headers, bullet points, "
            f"organized sections, and professional typography. "
            f"NO watermarks. Pure informational cheatsheet."
        )

        if len(prompt) > 2500:
            prompt = prompt[:2500]
        return prompt

    # ══════════════════════════════════════════════════════════════════
    #  Save generated image
    # ══════════════════════════════════════════════════════════════════
    def _save_image(self, title: str, image_bytes: bytes) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-") else "" for c in title[:40]
        ).replace(" ", "_")
        filename = f"cheatsheet_{safe_title}_{timestamp}.png"
        filepath = self.output_dir / filename

        image = Image.open(BytesIO(image_bytes))
        image.save(str(filepath), "PNG")
        self.logger.info(f"Image saved: {filepath} ({image.size})")
        return str(filepath)

    # ══════════════════════════════════════════════════════════════════
    #  HTML Cheatsheet Fallback (always works, no API needed)
    # ══════════════════════════════════════════════════════════════════
    def _generate_html_cheatsheet(
        self, title: str, content_summary: str, trend_data: Dict[str, Any]
    ) -> str:
        colors = trend_data.get("color_palette", {})
        design = trend_data.get("design_style", {})

        primary = colors.get("primary", "#2563EB")
        secondary = colors.get("secondary", "#7C3AED")
        accent = colors.get("accent", "#F59E0B")
        bg = colors.get("background", "#0F172A")
        text_color = colors.get("text", "#F8FAFC")

        # Parse content sections
        sections_html = ""
        lines = content_summary.split("\n")
        current_section = ""
        current_points = []

        for line in lines:
            line = line.strip()
            if line.startswith("Section:"):
                if current_section:
                    points_html = "".join(
                        f'<li>{p.strip()}</li>' for p in current_points
                    )
                    sections_html += f'''
                    <div class="section">
                        <h3>{current_section}</h3>
                        <ul>{points_html}</ul>
                    </div>'''
                current_section = line.replace("Section:", "").strip()
                current_points = []
            elif line.startswith("*") or line.startswith("-") or line.startswith("•"):
                current_points.append(line.lstrip("*-• "))

        # Last section
        if current_section:
            points_html = "".join(f'<li>{p}</li>' for p in current_points)
            sections_html += f'''
            <div class="section">
                <h3>{current_section}</h3>
                <ul>{points_html}</ul>
            </div>'''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: {bg};
            color: {text_color};
            padding: 40px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: linear-gradient(135deg, {primary}22, {secondary}22);
            border: 1px solid {primary}44;
            border-radius: 16px;
        }}
        .header h1 {{
            font-size: 2.5em;
            font-weight: 900;
            background: linear-gradient(135deg, {primary}, {secondary});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header .subtitle {{
            color: {text_color}99;
            font-size: 1em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 20px;
        }}
        .section {{
            background: {text_color}08;
            border: 1px solid {text_color}15;
            border-radius: 12px;
            padding: 24px;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .section:hover {{
            transform: translateY(-2px);
            border-color: {primary}66;
        }}
        .section h3 {{
            font-size: 1.15em;
            font-weight: 700;
            color: {accent};
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 2px solid {primary}33;
        }}
        .section ul {{
            list-style: none;
            padding: 0;
        }}
        .section li {{
            padding: 6px 0 6px 20px;
            position: relative;
            font-size: 0.92em;
            line-height: 1.5;
            color: {text_color}cc;
        }}
        .section li::before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: {primary};
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: {text_color}55;
            font-size: 0.85em;
        }}
        .badge {{
            display: inline-block;
            background: {primary}22;
            color: {primary};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p class="subtitle">AI-Generated Cheatsheet &bull; {datetime.now().strftime("%B %Y")}</p>
            <span class="badge">{design.get("theme", "Modern")} &bull; {design.get("mood", "Professional")}</span>
        </div>
        <div class="grid">
            {sections_html}
        </div>
        <div class="footer">
            Generated by AI Cheatsheet Pipeline &bull; Powered by Gemini
        </div>
    </div>
</body>
</html>'''

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-") else "" for c in title[:40]
        ).replace(" ", "_")
        filename = f"cheatsheet_{safe_title}_{timestamp}.html"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        self.logger.info(f"HTML cheatsheet saved: {filepath}")
        return str(filepath)
