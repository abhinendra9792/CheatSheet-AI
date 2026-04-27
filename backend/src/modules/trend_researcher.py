"""
Trend Researcher Module — Step 3: Trend + Style Upgrade
Uses Deep Research Pro to analyze latest trends, best practices,
and modern design recommendations for the cheatsheet topic.

Input:  Analysis from Step 1 (text) or Step 2 (image)
Output: Enriched data with trends, style guide, and content upgrades
"""
import asyncio
import json
from typing import Dict, Optional, Any
from google import genai
from google.genai import types
from src.utils.logger import trend_research_logger
from config.settings import config


class TrendResearchError(Exception):
    """Exception raised for trend research errors"""
    pass


class TrendResearcher:
    """
    Step 3: Research latest trends, best practices, and modern design
    styles for the cheatsheet topic using Deep Research Pro.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.DEEP_RESEARCH_API_KEY
        self.logger = trend_research_logger
        self.model_chain = config.DEEP_RESEARCH_MODELS

        if not self.api_key:
            raise TrendResearchError(
                "DEEP_RESEARCH_API_KEY not configured. "
                "Set it in backend/.env (Step 3 key)."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.logger.info(
            f"TrendResearcher initialized | models={self.model_chain} | SDK=google-genai"
        )

    # ──────────────────────────────────────────────────────────────────
    #  Core API call with fallback
    # ──────────────────────────────────────────────────────────────────
    async def _call_model(self, prompt: str, timeout: int = None) -> str:
        timeout = timeout or config.TEXT_GENERATION_TIMEOUT

        gen_config = types.GenerateContentConfig(
            temperature=0.4,
            top_p=0.9,
            max_output_tokens=config.MAX_OUTPUT_TOKENS,
        )

        for retry in range(config.MAX_RETRIES):
            errors = []

            for model_name in self.model_chain:
                try:
                    self.logger.info(
                        f"[Attempt {retry+1}/{config.MAX_RETRIES}] model={model_name}"
                    )
                    loop = asyncio.get_event_loop()
                    response = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda m=model_name: self.client.models.generate_content(
                                model=m, contents=prompt, config=gen_config,
                            ),
                        ),
                        timeout=timeout,
                    )
                    self.logger.info(f"✅ Response from {model_name}")
                    return response.text

                except asyncio.TimeoutError:
                    errors.append(f"{model_name}: timeout")
                    continue
                except Exception as e:
                    err = str(e)
                    if "429" in err or "RESOURCE_EXHAUSTED" in err:
                        self.logger.warning(f"⚠️ {model_name}: Rate limited, trying next...")
                        errors.append(f"{model_name}: rate limited")
                        await asyncio.sleep(3)
                        continue
                    errors.append(f"{model_name}: {err[:100]}")
                    continue

            # All models failed — retry with backoff if rate limited
            all_rate_limited = all("rate limited" in e for e in errors)
            if all_rate_limited and retry < config.MAX_RETRIES - 1:
                wait = 30 * (retry + 1)
                print(f"   ⏳ All models rate-limited. Waiting {wait}s before retry {retry+2}...")
                await asyncio.sleep(wait)
                continue
            elif retry < config.MAX_RETRIES - 1:
                await asyncio.sleep(5 * (retry + 1))
                continue

        raise TrendResearchError(f"All models failed after {config.MAX_RETRIES} retries: {' | '.join(errors)}")

    # ──────────────────────────────────────────────────────────────────
    #  Step 3: Research Trends + Style
    # ──────────────────────────────────────────────────────────────────
    async def research_trends(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3 — Trend + Style Upgrade: Takes the analysis from Step 1/2
        and enriches it with latest trends, best practices, and design
        recommendations.

        Args:
            analysis: Output dict from Step 1 (understand_user_input) or
                      Step 2 (analyze_image)

        Returns:
            Enriched dict with:
              - latest_trends, best_practices, content_upgrades,
                design_style, color_palette, layout_recommendation,
                visual_elements, enhanced_subtopics
        """
        topic = analysis.get("topic", "unknown")
        subtopics = analysis.get("subtopics", [])
        difficulty = analysis.get("difficulty", "intermediate")
        key_concepts = analysis.get("key_concepts", [])

        prompt = f"""You are a world-class design researcher and content strategist specializing in creating professional, visually stunning cheatsheets and infographics.

TOPIC: "{topic}"
SUBTOPICS: {json.dumps(subtopics)}
DIFFICULTY LEVEL: {difficulty}
KEY CONCEPTS: {json.dumps(key_concepts)}

Research and provide the following as JSON:

{{
    "latest_trends": [
        "List 5-7 latest trends, tools, or developments in this topic area (2025-2026)"
    ],
    "best_practices": [
        "List 5-7 current best practices professionals follow"
    ],
    "content_upgrades": [
        "List 5-7 additional subtopics or angles that should be included for a comprehensive cheatsheet"
    ],
    "enhanced_subtopics": [
        "Rewrite and expand the original subtopics with trend-aware improvements"
    ],
    "design_style": {{
        "theme": "Modern/Dark/Light/Gradient — recommend the best visual theme",
        "mood": "Professional/Playful/Technical/Elegant",
        "inspiration": "Describe the visual feel (e.g., 'Clean tech infographic with hub-and-spoke layout')"
    }},
    "color_palette": {{
        "primary": "#hex color",
        "secondary": "#hex color",
        "accent": "#hex color",
        "background": "#hex color",
        "text": "#hex color",
        "palette_name": "Name of the palette (e.g., 'Ocean Tech')"
    }},
    "layout_recommendation": {{
        "type": "hub-spoke | grid | columns | flow | mindmap | timeline",
        "sections": 6,
        "description": "Detailed layout description for the cheatsheet image"
    }},
    "visual_elements": [
        "List icons, diagrams, or visual elements to include (e.g., 'code snippet boxes', 'flow arrows', 'category badges')"
    ],
    "typography": {{
        "title_font": "Recommended font style for title",
        "body_font": "Recommended font style for body",
        "style_notes": "Typography guidance"
    }},
    "imagen_prompt_hints": "A detailed visual description to help generate the cheatsheet image — describe layout, colors, sections, icons, and overall aesthetic in 2-3 sentences"
}}

Respond with ONLY valid JSON, no markdown formatting or code blocks."""

        self.logger.info(f"[Step 3] Researching trends for: {topic}")
        raw_text = await self._call_model(prompt)
        result = self._extract_json(raw_text)
        self.logger.info(f"[Step 3] ✅ Trends researched — {len(result.get('latest_trends', []))} trends found")
        return result

    # ──────────────────────────────────────────────────────────────────
    #  JSON extraction
    # ──────────────────────────────────────────────────────────────────
    def _extract_json(self, text: str) -> Dict[str, Any]:
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
                        return json.loads(cleaned[start: i + 1])
                    except json.JSONDecodeError:
                        return {"raw_response": text}

        return {"raw_response": text}
