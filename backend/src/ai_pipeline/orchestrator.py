"""
CheatsheetPipeline — Main orchestrator for the complete 6-step pipeline.

Complete Flow:
  Step 1: Understand User (text)       → Gemini Pro     (GEMINI_PRO_API_KEY)
  Step 2: Analyze Old Image (optional) → Nano Banana    (GEMINI_NANO_API_KEY)
  Step 3: Trend + Style Upgrade        → Deep Research  (DEEP_RESEARCH_API_KEY)
  Step 4: Build Final Prompt           → Gemini Pro     (GEMINI_PRO_API_KEY)
  Step 5: Generate Content             → Gemini Pro     (GEMINI_PRO_API_KEY)
  Step 6: Generate Cheatsheet Image    → Imagen 4 Ultra (IMAGEN_API_KEY)
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from src.modules.text_generator import TextGenerator
from src.modules.image_analyzer import ImageAnalyzer
from src.modules.trend_researcher import TrendResearcher
from src.modules.image_generator import ImageGenerator
from src.modules.mindmap_renderer import MindmapRenderer
from src.modules.prompt_builder import PromptBuilder
from src.utils.logger import pipeline_logger
from config.settings import config


class CheatsheetPipelineError(Exception):
    pass


class CheatsheetPipeline:
    """
    Main orchestrator — coordinates all 6 steps of the pipeline.

    Text mode:  Step 1 → 3 → 4 → 5 → 6
    Image mode: Step 2 → 1 → 3 → 4 → 5 → 6
    """

    def __init__(self):
        self.logger = pipeline_logger
        self.prompt_builder = PromptBuilder()
        self.output_dir = config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1, 4, 5 → Gemini Pro
        self.text_generator = TextGenerator()

        # Lazy init for optional/separate-key modules
        self._image_analyzer = None    # Step 2
        self._trend_researcher = None  # Step 3
        self._image_generator = None   # Step 6
        self._mindmap_renderer = None   # Mind-map image renderer

    @property
    def image_analyzer(self) -> ImageAnalyzer:
        if self._image_analyzer is None:
            self._image_analyzer = ImageAnalyzer()
        return self._image_analyzer

    @property
    def trend_researcher(self) -> TrendResearcher:
        if self._trend_researcher is None:
            self._trend_researcher = TrendResearcher()
        return self._trend_researcher

    @property
    def image_generator(self) -> ImageGenerator:
        if self._image_generator is None:
            self._image_generator = ImageGenerator()
        return self._image_generator

    @property
    def mindmap_renderer(self) -> MindmapRenderer:
        if self._mindmap_renderer is None:
            self._mindmap_renderer = MindmapRenderer()
        return self._mindmap_renderer

    # ══════════════════════════════════════════════════════════════════
    #  TEXT MODE — Full pipeline from text prompt
    # ══════════════════════════════════════════════════════════════════
    async def generate_from_text_prompt(
        self,
        user_prompt: str,
        cheatsheet_title: Optional[str] = None,
        output_format: str = "txt",
        generate_image: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Text → Cheatsheet (Steps 1 → 3 → 4 → 5 → 6)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # ── STEP 1: Understand User ──────────────────────────────
            self._print_step(1, "Understanding your request", "Gemini Pro")
            user_analysis = await self.text_generator.understand_user_input(user_prompt)
            self._print_analysis(user_analysis)

            title = cheatsheet_title or user_analysis.get("suggested_title", user_prompt[:50])

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 3: Trend + Style Upgrade (non-fatal) ────────────
            self._print_step(3, "Researching trends & style", "Deep Research Pro")
            try:
                trend_data = await self.trend_researcher.research_trends(user_analysis)
                self._print_trends(trend_data)
            except Exception as e:
                print(f"   ⚠️ Step 3 failed (non-fatal): {e}")
                print(f"   📋 Using default style — pipeline continues...")
                trend_data = self._default_trend_data(user_analysis)

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 4: Build Final Prompt ───────────────────────────
            self._print_step(4, "Building optimized prompt", "Gemini Pro")
            final_prompt = self.prompt_builder.build_final_cheatsheet_prompt(
                user_analysis=user_analysis,
                trend_data=trend_data,
            )
            print(f"   ✅ Final prompt built ({len(final_prompt)} chars)")

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 5: Generate Content ─────────────────────────────
            self._print_step(5, "Generating cheatsheet content", "Gemini Pro")
            raw_content = await self.text_generator.generate_text(final_prompt, temperature=0.5)
            content_data = self.text_generator._extract_json(raw_content)
            sections = content_data.get("sections", [])
            print(f"   ✅ Content generated — {len(sections)} sections")

            # Save text output
            text_path = self._save_text_output(
                title, user_prompt, user_analysis, trend_data,
                content_data, timestamp, output_format
            )
            print(f"   💾 Text saved: {text_path}")

            result = {
                "title": title,
                "user_analysis": user_analysis,
                "trend_data": trend_data,
                "content": content_data,
                "text_output": text_path,
                "generation_time": timestamp,
                "mode": "text",
                "status": "success",
            }

            # ── STEP 6: Generate Cheatsheet Image ────────────────────
            if generate_image:
                await asyncio.sleep(config.RATE_LIMIT_DELAY)
                self._print_step(6, "Generating cheatsheet image", "Imagen 4 Ultra")
                try:
                    content_summary = self._summarize_content(content_data)
                    image_path = await self.image_generator.generate_cheatsheet_image(
                        title=title,
                        content_summary=content_summary,
                        trend_data=trend_data,
                    )
                    print(f"   ✅ Image generated: {image_path}")
                    result["image_output"] = image_path
                except Exception as e:
                    print(f"   ⚠️ Image generation failed (non-fatal): {e}")
                    result["image_output"] = None
                    result["image_error"] = str(e)

            self._print_success(result)
            return result

        except Exception as e:
            self.logger.error(f"Pipeline error: {e}", exc_info=True)
            raise CheatsheetPipelineError(f"Failed to generate cheatsheet: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  IMAGE MODE — Full pipeline from uploaded image
    # ══════════════════════════════════════════════════════════════════
    async def generate_from_image(
        self,
        image_path: str,
        output_format: str = "txt",
        generate_image: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Image → Cheatsheet (Steps 2 → 1 → 3 → 4 → 5 → 6)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # ── STEP 2: Analyze Old Image ────────────────────────────
            self._print_step(2, "Analyzing uploaded image", "Nano Banana Pro")
            image_analysis = await self.image_analyzer.analyze_image(image_path)
            self._print_image_analysis(image_analysis)

            # Build enriched prompt from image
            topic = image_analysis.get("topic", "Unknown")
            subtopics = image_analysis.get("subtopics", [])
            extracted = image_analysis.get("extracted_text", "")

            enriched_prompt = (
                f"Create an improved cheatsheet about '{topic}'. "
                f"Subtopics: {', '.join(subtopics)}. "
                f"Reference content: {extracted[:400]}"
            )

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 1: Understand Extracted Content ─────────────────
            self._print_step(1, "Understanding extracted content", "Gemini Pro")
            user_analysis = await self.text_generator.understand_user_input(enriched_prompt)
            title = user_analysis.get("suggested_title", topic)
            print(f"   ✅ Title: {title}")

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 3: Trend + Style Upgrade (non-fatal) ────────────
            self._print_step(3, "Researching trends & style", "Deep Research Pro")
            try:
                trend_data = await self.trend_researcher.research_trends(user_analysis)
                self._print_trends(trend_data)
            except Exception as e:
                print(f"   ⚠️ Step 3 failed (non-fatal): {e}")
                print(f"   📋 Using default style — pipeline continues...")
                trend_data = self._default_trend_data(user_analysis)

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 4: Build Final Prompt (with image context) ──────
            self._print_step(4, "Building optimized prompt", "Gemini Pro")
            final_prompt = self.prompt_builder.build_final_cheatsheet_prompt(
                user_analysis=user_analysis,
                trend_data=trend_data,
                image_analysis=image_analysis,
            )
            print(f"   ✅ Final prompt built ({len(final_prompt)} chars)")

            await asyncio.sleep(config.RATE_LIMIT_DELAY)

            # ── STEP 5: Generate Content ─────────────────────────────
            self._print_step(5, "Generating cheatsheet content", "Gemini Pro")
            raw_content = await self.text_generator.generate_text(final_prompt, temperature=0.5)
            content_data = self.text_generator._extract_json(raw_content)
            sections = content_data.get("sections", [])
            print(f"   ✅ Content generated — {len(sections)} sections")

            text_path = self._save_text_output(
                title, f"[Image: {image_path}]", user_analysis, trend_data,
                content_data, timestamp, output_format, image_analysis
            )
            print(f"   💾 Text saved: {text_path}")

            result = {
                "title": title,
                "image_analysis": image_analysis,
                "user_analysis": user_analysis,
                "trend_data": trend_data,
                "content": content_data,
                "text_output": text_path,
                "generation_time": timestamp,
                "mode": "image",
                "status": "success",
            }

            # ── STEP 6: Generate Cheatsheet Image ────────────────────
            if generate_image:
                await asyncio.sleep(config.RATE_LIMIT_DELAY)
                self._print_step(6, "Generating cheatsheet image", "Imagen 4 Ultra")
                try:
                    content_summary = self._summarize_content(content_data)
                    img_path = await self.image_generator.generate_cheatsheet_image(
                        title=title,
                        content_summary=content_summary,
                        trend_data=trend_data,
                    )
                    print(f"   ✅ Image generated: {img_path}")
                    result["image_output"] = img_path
                except Exception as e:
                    print(f"   ⚠️ Image generation failed (non-fatal): {e}")
                    result["image_output"] = None
                    result["image_error"] = str(e)

            self._print_success(result)
            return result

        except Exception as e:
            self.logger.error(f"Image pipeline error: {e}", exc_info=True)
            raise CheatsheetPipelineError(f"Failed to process image: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  COMBINED MODE — Text + Image together
    # ══════════════════════════════════════════════════════════════════
    async def generate_combined(
        self,
        user_prompt: str = "",
        image_path: Optional[str] = None,
        output_format: str = "txt",
        generate_image: bool = True,
    ) -> Dict[str, Any]:
        """
        Optimized pipeline: Does everything in 1-2 API calls max.
        - If image: Step 2 (image analysis) → Single mega-call (understand + content)
        - If text only: Single mega-call (understand + content)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_analysis = None

        try:
            # ── STEP 2: Analyze Image (if provided, 1 API call) ──────
            if image_path:
                self._print_step(2, "Analyzing uploaded image", "Nano Banana Pro")
                try:
                    image_analysis = await self.image_analyzer.analyze_image(image_path)
                    self._print_image_analysis(image_analysis)

                    img_topic = image_analysis.get("topic", "")
                    img_subtopics = image_analysis.get("subtopics", [])
                    img_text = image_analysis.get("extracted_text", "")

                    enrichment = (
                        f"\n\n[Image Analysis Context]\n"
                        f"Topic from image: {img_topic}\n"
                        f"Subtopics: {', '.join(img_subtopics)}\n"
                        f"Content: {img_text[:500]}\n"
                        f"Create an improved, modern version of this cheatsheet."
                    )
                    if user_prompt.strip():
                        user_prompt = f"{user_prompt}\n{enrichment}"
                    else:
                        user_prompt = (
                            f"Create an improved cheatsheet about '{img_topic}'. "
                            f"Subtopics: {', '.join(img_subtopics)}. "
                            f"Reference: {img_text[:400]}"
                        )
                except Exception as e:
                    print(f"   ⚠️ Image analysis failed (non-fatal): {e}")
                    if not user_prompt.strip():
                        # Create a fallback prompt from the filename
                        from pathlib import Path
                        fname = Path(image_path).stem.replace("_", " ").replace("-", " ")
                        user_prompt = f"Create a comprehensive cheatsheet. The user uploaded an image named '{fname}'. Generate a general technology cheatsheet with useful tips and best practices."
                        print(f"   📋 Using fallback prompt from filename")

                await asyncio.sleep(2)

            # ── SINGLE MEGA-CALL: Understand + Generate Content (1 API call) ──
            self._print_step(1, "Generating cheatsheet (single-call mode)", "Gemini Multi-Key")
            print(f"   📝 Prompt: {user_prompt[:100]}...")

            mega_prompt = f"""You are an expert cheatsheet creator. The user wants a cheatsheet about the following topic.

USER REQUEST: {user_prompt}

Analyze the request and generate a complete cheatsheet. Return ONLY valid JSON with this exact structure:
{{
    "topic": "main topic name",
    "difficulty": "beginner/intermediate/advanced",
    "subtopics": ["subtopic1", "subtopic2", ...],
    "suggested_title": "Catchy Cheatsheet Title",
    "tags": ["tag1", "tag2", "tag3"],
    "latest_trends": ["trend 1 in this field", "trend 2", "trend 3"],
    "summary": "A 2-3 sentence overview of the cheatsheet content",
    "sections": [
        {{
            "title": "Section Title",
            "key_points": ["point 1", "point 2", "point 3", "point 4"],
            "pro_tip": "A practical tip for this section",
            "code_example": "optional code snippet or empty string"
        }},
        ... (create 5-8 sections)
    ]
}}

Requirements:
- Create 5-8 comprehensive sections with 3-5 key points each
- Include practical pro tips
- Add code examples where relevant
- Include current trends and best practices
- Make content detailed and actionable
- Return ONLY the JSON, no markdown fences"""

            raw_content = await self.text_generator.generate_text(mega_prompt, temperature=0.5)
            mega_data = self.text_generator._extract_json(raw_content)

            # Extract user_analysis from mega response
            user_analysis = {
                "topic": mega_data.get("topic", user_prompt[:50]),
                "difficulty": mega_data.get("difficulty", "intermediate"),
                "subtopics": mega_data.get("subtopics", []),
                "suggested_title": mega_data.get("suggested_title", user_prompt[:50]),
            }
            title = user_analysis["suggested_title"]
            self._print_analysis(user_analysis)

            # Extract content_data
            content_data = {
                "sections": mega_data.get("sections", []),
                "summary": mega_data.get("summary", ""),
                "tags": mega_data.get("tags", []),
            }
            sections = content_data.get("sections", [])
            print(f"   ✅ Generated {len(sections)} sections in single call!")

            # Use default trend data (no extra API call needed)
            trend_data = self._default_trend_data(user_analysis)
            trend_data["latest_trends"] = mega_data.get("latest_trends", trend_data["latest_trends"])

            # Save output
            text_path = self._save_text_output(
                title, user_prompt, user_analysis, trend_data,
                content_data, timestamp, output_format, image_analysis
            )
            print(f"   💾 Saved: {text_path}")

            mode = "combined" if image_path else "text"
            result = {
                "title": title,
                "user_analysis": user_analysis,
                "trend_data": trend_data,
                "content": content_data,
                "text_output": text_path,
                "generation_time": timestamp,
                "mode": mode,
                "status": "success",
            }
            if image_analysis:
                result["image_analysis"] = image_analysis

            # ── STEP 6: Render Mind-Map Image (local, no API needed) ──
            self._print_step(6, "Rendering mind-map image", "Pillow Renderer")
            try:
                mindmap_path = self.mindmap_renderer.render(
                    title=title,
                    user_analysis=user_analysis,
                    trend_data=trend_data,
                    content_data=content_data,
                    timestamp=timestamp,
                )
                print(f"   ✅ Mind-map image rendered: {mindmap_path}")
                result["image_output"] = mindmap_path
            except Exception as e:
                print(f"   ⚠️ Mind-map render failed (non-fatal): {e}")
                result["image_output"] = None

            self._print_success(result)
            return result

        except Exception as e:
            self.logger.error(f"Combined pipeline error: {e}", exc_info=True)
            raise CheatsheetPipelineError(f"Failed to generate cheatsheet: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════════════
    def _summarize_content(self, content_data: Dict) -> str:
        """Condense content_data into a text summary for Imagen prompt."""
        sections = content_data.get("sections", [])
        lines = []
        for s in sections:
            title = s.get("title", "")
            points = s.get("key_points", [])
            lines.append(f"Section: {title}")
            for p in points[:3]:
                lines.append(f"  • {p}")
        return "\n".join(lines)

    @staticmethod
    def _default_trend_data(user_analysis: Dict) -> Dict[str, Any]:
        """
        Fallback trend data when Step 3 fails (rate limits, etc).
        Provides sensible defaults so Steps 4-6 can still work.
        """
        topic = user_analysis.get("topic", "Technology")
        subtopics = user_analysis.get("subtopics", [])
        return {
            "latest_trends": [f"Latest developments in {topic}"],
            "best_practices": [f"Industry best practices for {topic}"],
            "content_upgrades": subtopics[:3],
            "enhanced_subtopics": subtopics,
            "design_style": {
                "theme": "Modern dark",
                "mood": "Professional and clean",
                "inspiration": "Clean tech infographic with organized grid layout",
            },
            "color_palette": {
                "primary": "#2563EB",
                "secondary": "#7C3AED",
                "accent": "#F59E0B",
                "background": "#0F172A",
                "text": "#F8FAFC",
                "palette_name": "Tech Blue",
            },
            "layout_recommendation": {
                "type": "grid",
                "sections": 6,
                "description": "Clean grid layout with organized sections",
            },
            "visual_elements": ["section headers", "bullet points", "code boxes"],
            "typography": {
                "title_font": "sans-serif bold",
                "body_font": "sans-serif",
                "style_notes": "Clean and readable",
            },
            "imagen_prompt_hints": (
                f"A professional, modern cheatsheet infographic about {topic} "
                f"with a dark blue background, organized grid sections, "
                f"clean typography, and visual hierarchy."
            ),
        }

    def _save_text_output(
        self, title, source, user_analysis, trend_data,
        content_data, timestamp, fmt, image_analysis=None,
    ) -> str:
        """Save the cheatsheet output — HTML or plain text."""
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-") else "" for c in title[:50]
        ).replace(" ", "_")
        output_file = self.output_dir / f"cheatsheet_{safe_title}_{timestamp}.{fmt}"

        if fmt == "html":
            html = self._build_html_cheatsheet(title, user_analysis, trend_data, content_data, image_analysis)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
        else:
            text = self._build_text_cheatsheet(title, source, user_analysis, trend_data, content_data, image_analysis)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

        return str(output_file)

    def _build_html_cheatsheet(self, title, user_analysis, trend_data, content_data, image_analysis=None):
        """Build a mind-map / infographic style HTML cheatsheet with images."""
        topic = user_analysis.get("topic", "")
        difficulty = user_analysis.get("difficulty", "")
        subtopics = user_analysis.get("subtopics", [])
        sections = content_data.get("sections", [])
        summary = content_data.get("summary", "")
        trends = trend_data.get("latest_trends", [])
        tags = content_data.get("tags", [])

        # Color palette for sections
        palette = [
            {"bg": "rgba(59,130,246,0.08)", "border": "#3b82f6", "text": "#60a5fa", "glow": "59,130,246"},
            {"bg": "rgba(16,185,129,0.08)", "border": "#10b981", "text": "#34d399", "glow": "16,185,129"},
            {"bg": "rgba(245,158,11,0.08)", "border": "#f59e0b", "text": "#fbbf24", "glow": "245,158,11"},
            {"bg": "rgba(139,92,246,0.08)", "border": "#8b5cf6", "text": "#a78bfa", "glow": "139,92,246"},
            {"bg": "rgba(244,63,94,0.08)", "border": "#f43f5e", "text": "#fb7185", "glow": "244,63,94"},
            {"bg": "rgba(6,182,212,0.08)", "border": "#06b6d4", "text": "#22d3ee", "glow": "6,182,212"},
            {"bg": "rgba(234,179,8,0.08)", "border": "#eab308", "text": "#facc15", "glow": "234,179,8"},
            {"bg": "rgba(99,102,241,0.08)", "border": "#6366f1", "text": "#818cf8", "glow": "99,102,241"},
        ]

        # Section emojis
        emojis = ["🧠", "⚡", "🔧", "📊", "🚀", "🛡️", "💡", "🎯", "📦", "🔬"]

        # SVG pattern generators for each section
        import random
        random.seed(hash(topic or "tech"))  # deterministic but unique per topic

        def _make_svg_pattern(idx, rgb, hex_color):
            """Generate a unique abstract SVG illustration per section."""
            patterns = [
                # Circuit board
                f'''<svg viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
                    <rect width="400" height="140" fill="rgba({rgb},0.06)"/>
                    <circle cx="60" cy="70" r="25" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.4"/>
                    <circle cx="60" cy="70" r="8" fill="{hex_color}" opacity="0.3"/>
                    <line x1="85" y1="70" x2="160" y2="70" stroke="{hex_color}" stroke-width="1.5" opacity="0.3"/>
                    <circle cx="160" cy="70" r="4" fill="{hex_color}" opacity="0.5"/>
                    <line x1="164" y1="70" x2="220" y2="40" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <line x1="164" y1="70" x2="220" y2="100" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <circle cx="220" cy="40" r="3" fill="{hex_color}" opacity="0.4"/>
                    <circle cx="220" cy="100" r="3" fill="{hex_color}" opacity="0.4"/>
                    <rect x="280" y="50" width="40" height="40" rx="8" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.3"/>
                    <circle cx="300" cy="70" r="10" fill="{hex_color}" opacity="0.15"/>
                    <line x1="240" y1="40" x2="280" y2="55" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <line x1="240" y1="100" x2="280" y2="85" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <circle cx="360" cy="30" r="15" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <circle cx="370" cy="110" r="20" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.15"/>
                </svg>''',
                # Hexagon grid
                f'''<svg viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
                    <rect width="400" height="140" fill="rgba({rgb},0.06)"/>
                    <polygon points="70,20 100,35 100,65 70,80 40,65 40,35" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.35"/>
                    <polygon points="70,20 100,35 100,65 70,80 40,65 40,35" fill="{hex_color}" opacity="0.08"/>
                    <polygon points="130,50 160,65 160,95 130,110 100,95 100,65" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <polygon points="200,15 230,30 230,60 200,75 170,60 170,30" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.3"/>
                    <polygon points="200,15 230,30 230,60 200,75 170,60 170,30" fill="{hex_color}" opacity="0.06"/>
                    <polygon points="270,60 300,75 300,105 270,120 240,105 240,75" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.25"/>
                    <polygon points="340,25 370,40 370,70 340,85 310,70 310,40" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <circle cx="70" cy="50" r="12" fill="{hex_color}" opacity="0.12"/>
                    <circle cx="200" cy="45" r="10" fill="{hex_color}" opacity="0.1"/>
                </svg>''',
                # Wave pattern
                f'''<svg viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
                    <rect width="400" height="140" fill="rgba({rgb},0.06)"/>
                    <path d="M0,70 Q50,30 100,70 Q150,110 200,70 Q250,30 300,70 Q350,110 400,70" fill="none" stroke="{hex_color}" stroke-width="2" opacity="0.3"/>
                    <path d="M0,90 Q50,50 100,90 Q150,130 200,90 Q250,50 300,90 Q350,130 400,90" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.15"/>
                    <path d="M0,50 Q50,10 100,50 Q150,90 200,50 Q250,10 300,50 Q350,90 400,50" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.15"/>
                    <circle cx="100" cy="70" r="6" fill="{hex_color}" opacity="0.4"/>
                    <circle cx="200" cy="70" r="8" fill="{hex_color}" opacity="0.3"/>
                    <circle cx="300" cy="70" r="6" fill="{hex_color}" opacity="0.4"/>
                </svg>''',
                # Data nodes
                f'''<svg viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
                    <rect width="400" height="140" fill="rgba({rgb},0.06)"/>
                    <circle cx="80" cy="50" r="20" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.35"/>
                    <circle cx="80" cy="50" r="6" fill="{hex_color}" opacity="0.3"/>
                    <circle cx="200" cy="90" r="25" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.3"/>
                    <circle cx="200" cy="90" r="8" fill="{hex_color}" opacity="0.25"/>
                    <circle cx="320" cy="50" r="18" fill="none" stroke="{hex_color}" stroke-width="1.5" opacity="0.3"/>
                    <circle cx="320" cy="50" r="5" fill="{hex_color}" opacity="0.35"/>
                    <line x1="100" y1="50" x2="175" y2="90" stroke="{hex_color}" stroke-width="1.5" opacity="0.25" stroke-dasharray="4"/>
                    <line x1="225" y1="90" x2="302" y2="50" stroke="{hex_color}" stroke-width="1.5" opacity="0.25" stroke-dasharray="4"/>
                    <circle cx="140" cy="110" r="10" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                    <circle cx="280" cy="110" r="12" fill="none" stroke="{hex_color}" stroke-width="1" opacity="0.2"/>
                </svg>''',
            ]
            return patterns[idx % len(patterns)]

        # Build branch nodes with SVG illustrations
        branch_html = ""
        for i, section in enumerate(sections):
            c = palette[i % len(palette)]
            emoji = emojis[i % len(emojis)]
            sec_title = section.get("title", f"Section {i+1}")
            points = section.get("key_points", [])
            tip = section.get("pro_tip", "")
            code = section.get("code_example", "")
            content = section.get("content", "")

            svg_illustration = _make_svg_pattern(i, c["glow"], c["border"])

            points_html = "".join(
                f'<li><span class="bullet" style="color:{c["border"]}">▸</span> {p}</li>'
                for p in points
            )
            tip_html = f'<div class="tip-box" style="border-color:{c["border"]};background:rgba({c["glow"]},0.05)">💡 {tip}</div>' if tip else ""
            code_html = f'<pre><code>{code}</code></pre>' if code else ""

            branch_html += f'''
            <div class="branch-node" style="--accent:{c['border']};--accent-rgb:{c['glow']};--accent-text:{c['text']}">
                <div class="node-connector"></div>
                <div class="node-number">{i+1}</div>
                <div class="node-card">
                    <div class="node-img">
                        {svg_illustration}
                    </div>
                    <div class="node-header">
                        <span class="node-emoji">{emoji}</span>
                        <h3>{sec_title}</h3>
                    </div>
                    <ul class="node-points">{points_html}</ul>
                    {code_html}
                    {tip_html}
                </div>
            </div>'''

        # Hero SVG banner
        hero_svg = f'''<svg viewBox="0 0 1200 200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="hero-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.15"/>
                    <stop offset="50%" style="stop-color:#8b5cf6;stop-opacity:0.1"/>
                    <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:0.15"/>
                </linearGradient>
            </defs>
            <rect width="1200" height="200" fill="url(#hero-grad)"/>
            <circle cx="100" cy="100" r="60" fill="none" stroke="#3b82f6" stroke-width="1.5" opacity="0.2"/>
            <circle cx="100" cy="100" r="30" fill="#3b82f6" opacity="0.08"/>
            <circle cx="300" cy="60" r="40" fill="none" stroke="#8b5cf6" stroke-width="1" opacity="0.2"/>
            <circle cx="500" cy="140" r="50" fill="none" stroke="#06b6d4" stroke-width="1.5" opacity="0.15"/>
            <circle cx="700" cy="80" r="35" fill="none" stroke="#f59e0b" stroke-width="1" opacity="0.2"/>
            <circle cx="900" cy="120" r="45" fill="none" stroke="#10b981" stroke-width="1" opacity="0.15"/>
            <circle cx="1100" cy="70" r="55" fill="none" stroke="#8b5cf6" stroke-width="1.5" opacity="0.2"/>
            <line x1="130" y1="80" x2="270" y2="60" stroke="#3b82f6" stroke-width="1" opacity="0.15" stroke-dasharray="6"/>
            <line x1="340" y1="70" x2="460" y2="130" stroke="#8b5cf6" stroke-width="1" opacity="0.15" stroke-dasharray="6"/>
            <line x1="540" y1="130" x2="670" y2="85" stroke="#06b6d4" stroke-width="1" opacity="0.15" stroke-dasharray="6"/>
            <line x1="735" y1="90" x2="865" y2="115" stroke="#f59e0b" stroke-width="1" opacity="0.1" stroke-dasharray="6"/>
            <line x1="945" y1="110" x2="1060" y2="80" stroke="#10b981" stroke-width="1" opacity="0.1" stroke-dasharray="6"/>
            <path d="M0,180 Q200,130 400,170 Q600,210 800,160 Q1000,120 1200,170" fill="none" stroke="#3b82f6" stroke-width="1" opacity="0.1"/>
        </svg>'''

        # Trend chips
        trend_chips = "".join(f'<span class="trend-chip">→ {t}</span>' for t in trends[:6])
        trends_section = f'<div class="trends-ring"><h4>🔥 Trends</h4><div class="trend-list">{trend_chips}</div></div>' if trends else ""

        # Tags
        tag_chips = "".join(f'<span class="tag-chip">{t}</span>' for t in (tags or subtopics)[:12])
        tags_section = f'<div class="tags-area">{tag_chips}</div>' if tag_chips else ""

        # Summary
        summary_section = f'<div class="summary-box"><h4>📝 Summary</h4><p>{summary}</p></div>' if summary else ""

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #060a14;
            --bg-card: rgba(15,23,42,0.7);
            --border: rgba(255,255,255,0.06);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        /* ── Background Pattern ── */
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(circle at 20% 20%, rgba(59,130,246,0.06) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139,92,246,0.06) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(6,182,212,0.04) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }}
        /* ── Grid dots ── */
        body::after {{
            content: '';
            position: fixed;
            inset: 0;
            background-image: radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 32px 32px;
            pointer-events: none;
            z-index: 0;
        }}

        /* ══════════ HERO / HUB ══════════ */
        .hero {{
            position: relative;
            z-index: 1;
            text-align: center;
            padding: 60px 24px 40px;
        }}
        .hub {{
            display: inline-block;
            position: relative;
            padding: 36px 60px;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(139,92,246,0.12), rgba(6,182,212,0.12));
            border: 1.5px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            box-shadow: 0 0 80px rgba(59,130,246,0.1), 0 0 160px rgba(139,92,246,0.05);
        }}
        .hub::before {{
            content: '';
            position: absolute;
            inset: -2px;
            border-radius: 26px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4);
            z-index: -1;
            opacity: 0.3;
            filter: blur(1px);
        }}
        .hub h1 {{
            font-size: clamp(1.5rem, 4vw, 2.4rem);
            font-weight: 900;
            background: linear-gradient(135deg, #60a5fa, #a78bfa, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }}
        .hub-meta {{
            margin-top: 14px;
            color: var(--text-secondary);
            font-size: 0.88rem;
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .hub-meta span {{ display: flex; align-items: center; gap: 4px; }}
        .hub-pulse {{
            position: absolute;
            inset: -4px;
            border-radius: 28px;
            border: 1px solid rgba(59,130,246,0.2);
            animation: pulse 3s ease-in-out infinite;
        }}
        @keyframes pulse {{
            0%,100% {{ opacity:0.3; transform:scale(1); }}
            50% {{ opacity:0.1; transform:scale(1.02); }}
        }}

        /* ══════════ BRANCHES ══════════ */
        .container {{ position: relative; z-index:1; max-width:1200px; margin:0 auto; padding:0 24px 60px; }}

        .branches {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 24px;
            margin-top: 40px;
        }}

        .branch-node {{
            position: relative;
        }}
        .node-connector {{
            position: absolute;
            top: 0;
            left: 32px;
            width: 3px;
            height: 100%;
            background: linear-gradient(to bottom, var(--accent), transparent);
            opacity: 0.2;
            border-radius: 3px;
        }}
        .node-number {{
            position: absolute;
            top: -8px;
            left: 18px;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--bg-primary);
            border: 2px solid var(--accent);
            color: var(--accent-text);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.82rem;
            z-index: 2;
            box-shadow: 0 0 16px rgba(var(--accent-rgb), 0.3);
        }}
        .node-card {{
            margin-left: 60px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
            backdrop-filter: blur(12px);
        }}
        .node-card:hover {{
            transform: translateX(4px);
            border-color: rgba(var(--accent-rgb), 0.3);
            box-shadow: 0 8px 40px rgba(var(--accent-rgb), 0.1);
        }}
        .node-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;
        }}
        .node-emoji {{ font-size: 1.4rem; }}
        .node-header h3 {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-text);
        }}
        .node-points {{
            list-style: none;
            padding: 0;
        }}
        .node-points li {{
            padding: 5px 0;
            font-size: 0.88rem;
            color: var(--text-secondary);
            line-height: 1.5;
            display: flex;
            gap: 6px;
        }}
        .bullet {{ font-weight: 700; flex-shrink:0; }}
        pre {{
            margin-top: 12px;
            background: rgba(0,0,0,0.4);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            overflow-x: auto;
        }}
        code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: #e2e8f0;
        }}
        .tip-box {{
            margin-top: 12px;
            padding: 10px 14px;
            border-left: 3px solid;
            border-radius: 0 10px 10px 0;
            font-size: 0.82rem;
            color: #fbbf24;
        }}

        /* ══════════ TRENDS ══════════ */
        .trends-ring {{
            margin: 40px auto;
            max-width: 900px;
            padding: 28px;
            background: rgba(245,158,11,0.04);
            border: 1px solid rgba(245,158,11,0.12);
            border-radius: 20px;
            text-align: center;
        }}
        .trends-ring h4 {{
            font-size: 1.1rem;
            margin-bottom: 14px;
            color: #fbbf24;
        }}
        .trend-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }}
        .trend-chip {{
            padding: 6px 14px;
            background: rgba(245,158,11,0.08);
            border: 1px solid rgba(245,158,11,0.15);
            border-radius: 999px;
            font-size: 0.78rem;
            color: #fbbf24;
        }}

        /* ══════════ TAGS ══════════ */
        .tags-area {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin: 24px 0;
        }}
        .tag-chip {{
            padding: 4px 14px;
            background: rgba(139,92,246,0.08);
            border: 1px solid rgba(139,92,246,0.15);
            border-radius: 999px;
            font-size: 0.76rem;
            color: #a78bfa;
        }}

        /* ══════════ SUMMARY ══════════ */
        .summary-box {{
            max-width: 800px;
            margin: 36px auto;
            padding: 28px;
            background: rgba(6,182,212,0.04);
            border: 1px solid rgba(6,182,212,0.12);
            border-radius: 20px;
            text-align: center;
        }}
        .summary-box h4 {{
            font-size: 1.1rem;
            color: #22d3ee;
            margin-bottom: 10px;
        }}
        .summary-box p {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.7;
        }}

        /* ══════════ IMAGES ══════════ */
        .node-img {{
            margin: -24px -24px 16px -24px;
            border-radius: 16px 16px 0 0;
            overflow: hidden;
            height: 140px;
        }}
        .node-img svg {{
            width: 100%;
            height: 100%;
            opacity: 0.8;
            transition: opacity 0.3s;
        }}
        .node-card:hover .node-img svg {{ opacity: 1; }}
        .hero-banner {{
            width: 100%;
            max-width: 1000px;
            margin: 0 auto 20px;
            border-radius: 20px;
            overflow: hidden;
            height: 180px;
            position: relative;
        }}
        .hero-banner svg {{
            width: 100%;
            height: 100%;
        }}
        .hero-banner::after {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(to bottom, transparent, var(--bg-primary));
        }}

        /* ══════════ FOOTER ══════════ */
        .footer {{
            text-align: center;
            padding: 40px 24px;
            color: var(--text-muted);
            font-size: 0.78rem;
            border-top: 1px solid var(--border);
        }}
        .footer a {{ color: #60a5fa; text-decoration: none; }}

        @media (max-width: 768px) {{
            .branches {{ grid-template-columns: 1fr; }}
            .hub {{ padding: 24px 32px; }}
        }}
        @media print {{
            body {{ background: #fff; color: #1e293b; }}
            body::before, body::after {{ display: none; }}
            .node-card {{ border: 1px solid #e2e8f0; background: #f8fafc; }}
        }}
    </style>
</head>
<body>
    <!-- ══ CENTRAL HUB ══ -->
    <div class="hero">
        <div class="hub">
            <div class="hub-pulse"></div>
            <h1>{title}</h1>
            <div class="hub-meta">
                <span>📚 {topic}</span>
                <span>📊 {difficulty}</span>
                <span>📄 {len(sections)} Sections</span>
                <span>⏰ {datetime.now().strftime('%b %Y')}</span>
            </div>
        </div>
    </div>

    <!-- ══ HERO BANNER ══ -->
    <div class="hero-banner">
        {hero_svg}
    </div>

    <div class="container">
        {tags_section}
        {trends_section}

        <!-- ══ BRANCH NODES ══ -->
        <div class="branches">
            {branch_html}
        </div>

        {summary_section}
    </div>

    <div class="footer">
        Generated by <a href="#">AI Cheatsheet Pipeline</a> • Powered by Gemini • {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
</body>
</html>'''

    def _build_text_cheatsheet(self, title, source, user_analysis, trend_data, content_data, image_analysis=None):
        """Build plain text cheatsheet (fallback)."""
        sep = "=" * 70
        lines = [
            sep,
            f"  📚 {title}",
            sep,
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Source:     {source[:100]}",
            f"  Topic:      {user_analysis.get('topic', 'N/A')}",
            f"  Difficulty: {user_analysis.get('difficulty', 'N/A')}",
            sep, "",
        ]

        trends = trend_data.get("latest_trends", [])
        if trends:
            lines.append("🔥 LATEST TRENDS")
            lines.append("-" * 70)
            for t in trends:
                lines.append(f"  • {t}")
            lines.append("")

        if image_analysis:
            lines.append("📸 IMAGE ANALYSIS")
            lines.append("-" * 70)
            lines.append(f"  Original Topic: {image_analysis.get('topic', 'N/A')}")
            lines.append("")

        sections = content_data.get("sections", [])
        for i, section in enumerate(sections, 1):
            lines.append(f"📋 SECTION {i}: {section.get('title', 'Untitled')}")
            lines.append("-" * 70)
            for point in section.get("key_points", []):
                lines.append(f"  • {point}")
            content = section.get("content", "")
            if content:
                lines.append(f"\n  {content[:500]}")
            tip = section.get("pro_tip", "")
            if tip:
                lines.append(f"\n  💡 Pro Tip: {tip}")
            code = section.get("code_example", "")
            if code:
                lines.append(f"\n  ```\n  {code}\n  ```")
            lines.append("")

        summary = content_data.get("summary", "")
        if summary:
            lines.append("📝 SUMMARY")
            lines.append("-" * 70)
            lines.append(f"  {summary}")
            lines.append("")

        lines.extend([sep, "  END OF CHEATSHEET", sep])
        return "\n".join(lines)

    # ── Print helpers ────────────────────────────────────────────────
    @staticmethod
    def _print_step(num, desc, model):
        print(f"\n{'=' * 60}")
        step_icons = {1: "🧠", 2: "📸", 3: "🔍", 4: "🔧", 5: "📝", 6: "🎨"}
        icon = step_icons.get(num, "▶️")
        print(f"{icon} STEP {num}: {desc} ({model})...")
        print("=" * 60)

    @staticmethod
    def _print_analysis(a):
        print(f"\n📋 Analysis:")
        print(f"   Topic:      {a.get('topic', 'N/A')}")
        print(f"   Subtopics:  {', '.join(a.get('subtopics', []))}")
        print(f"   Difficulty: {a.get('difficulty', 'N/A')}")
        print(f"   Title:      {a.get('suggested_title', 'N/A')}")

    @staticmethod
    def _print_trends(t):
        trends = t.get("latest_trends", [])
        palette = t.get("color_palette", {})
        layout = t.get("layout_recommendation", {})
        print(f"\n🔍 Trends: {len(trends)} found")
        for tr in trends[:3]:
            print(f"   • {tr}")
        if len(trends) > 3:
            print(f"   ... and {len(trends) - 3} more")
        print(f"   🎨 Palette: {palette.get('palette_name', 'N/A')}")
        print(f"   📐 Layout:  {layout.get('type', 'N/A')}")

    @staticmethod
    def _print_image_analysis(a):
        print(f"\n📸 Image Analysis:")
        print(f"   Topic:    {a.get('topic', 'N/A')}")
        print(f"   Sections: {a.get('structure', {}).get('num_sections', 'N/A')}")
        subs = a.get("subtopics", [])
        if subs:
            print(f"   Topics:   {', '.join(subs[:5])}")

    @staticmethod
    def _print_success(result):
        print(f"\n{'=' * 60}")
        print("🎉 PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"   Title:      {result['title']}")
        print(f"   Text:       {result.get('text_output', 'N/A')}")
        print(f"   Image:      {result.get('image_output', 'N/A')}")
        print(f"   Mode:       {result['mode']}")
        print(f"   Time:       {result['generation_time']}")
        print()


def create_pipeline() -> CheatsheetPipeline:
    return CheatsheetPipeline()
