"""
PromptBuilder — Step 4: Build Final Prompt (VERY IMPORTANT)

Takes all data from Steps 1-3 and builds the optimized final prompt
that Step 5 (content generation) and Step 6 (image generation) will use.
"""
import json
from typing import Dict, Any, Optional


class PromptBuilder:
    """Builds specialized prompts for each stage of cheatsheet generation."""

    # ══════════════════════════════════════════════════════════════════
    #  Step 4: Build the FINAL optimized prompt
    # ══════════════════════════════════════════════════════════════════
    def build_final_cheatsheet_prompt(
        self,
        user_analysis: Dict[str, Any],
        trend_data: Dict[str, Any],
        image_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Step 4 — Build Final Prompt: Combines ALL pipeline data into
        one optimized master prompt for content generation.

        Args:
            user_analysis: Output from Step 1 (understand_user_input)
            trend_data: Output from Step 3 (research_trends)
            image_analysis: Optional output from Step 2 (analyze_image)

        Returns:
            The final optimized prompt for Step 5 content generation
        """
        topic = user_analysis.get("topic", "Unknown")
        title = user_analysis.get("suggested_title", topic)
        subtopics = user_analysis.get("subtopics", [])
        difficulty = user_analysis.get("difficulty", "intermediate")
        audience = user_analysis.get("audience", "developers and tech professionals")
        key_concepts = user_analysis.get("key_concepts", [])

        # Trend enrichments from Step 3
        latest_trends = trend_data.get("latest_trends", [])
        best_practices = trend_data.get("best_practices", [])
        content_upgrades = trend_data.get("content_upgrades", [])
        enhanced_subtopics = trend_data.get("enhanced_subtopics", subtopics)
        design_style = trend_data.get("design_style", {})
        layout = trend_data.get("layout_recommendation", {})

        # Image analysis enrichment (if user uploaded an image)
        image_context = ""
        if image_analysis:
            img_topic = image_analysis.get("topic", "")
            img_text = image_analysis.get("extracted_text", "")
            img_sections = image_analysis.get("structure", {}).get("sections", [])
            improvements = image_analysis.get("suggested_improvements", [])

            image_context = f"""
REFERENCE IMAGE ANALYSIS:
- Original topic: {img_topic}
- Sections found: {json.dumps(img_sections)}
- Suggested improvements: {json.dumps(improvements)}
- Extracted key content: {img_text[:300]}
Use this as reference to CREATE BETTER, MORE COMPREHENSIVE content. Do NOT copy — improve.
"""

        # Build the master prompt
        prompt = f"""You are a world-class technical writer creating a comprehensive, professional cheatsheet.

═══════════════════════════════════════════════
CHEATSHEET SPECIFICATION
═══════════════════════════════════════════════

TITLE: {title}
TOPIC: {topic}
DIFFICULTY: {difficulty}
TARGET AUDIENCE: {audience}

KEY CONCEPTS TO COVER:
{json.dumps(key_concepts, indent=2)}

ENHANCED SUBTOPICS (trend-aware):
{json.dumps(enhanced_subtopics, indent=2)}

LATEST TRENDS (2025-2026):
{json.dumps(latest_trends, indent=2)}

BEST PRACTICES:
{json.dumps(best_practices, indent=2)}

ADDITIONAL TOPICS TO INCLUDE:
{json.dumps(content_upgrades, indent=2)}
{image_context}
═══════════════════════════════════════════════
LAYOUT SPECIFICATION
═══════════════════════════════════════════════

Layout type: {layout.get('type', 'grid')}
Number of sections: {layout.get('sections', 6)}
Design mood: {design_style.get('mood', 'Professional')}

═══════════════════════════════════════════════
CONTENT GENERATION RULES
═══════════════════════════════════════════════

Generate the COMPLETE cheatsheet content following these rules:

1. Create exactly {layout.get('sections', 6)} major sections
2. Each section must have:
   - A clear, concise section TITLE (3-8 words)
   - 3-5 KEY POINTS as bullet points
   - Practical EXAMPLES or code snippets where relevant
   - A PRO TIP or best practice note
3. Content must be:
   - Original (not copied from any source)
   - Up-to-date with 2025-2026 trends
   - Practical and actionable
   - Appropriate for {difficulty} level
4. Include the latest trends and best practices listed above
5. Use clear, direct language — no fluff
6. Format for visual presentation (short paragraphs, bullet points, headers)

OUTPUT FORMAT — respond with ONLY valid JSON:
{{
    "title": "{title}",
    "sections": [
        {{
            "section_number": 1,
            "title": "Section Title",
            "key_points": ["point 1", "point 2", "point 3"],
            "content": "Detailed section content with examples...",
            "pro_tip": "A practical pro tip for this section",
            "code_example": "Optional code snippet if relevant"
        }}
    ],
    "summary": "A 2-3 sentence summary of the entire cheatsheet",
    "tags": ["tag1", "tag2", "tag3"]
}}

Respond with ONLY valid JSON, no markdown formatting or code blocks."""

        return prompt

    # ══════════════════════════════════════════════════════════════════
    #  Helper prompts (used by Steps 1 and orchestrator)
    # ══════════════════════════════════════════════════════════════════
    def build_title_generation_prompt(self, topic: str) -> str:
        """Generate a prompt for creating an engaging title."""
        return f"""You are a technical writer. Create a concise, engaging title for a cheatsheet about "{topic}".
The title should be:
- Clear and descriptive
- 3-8 words maximum
- Easy to remember
- Professional

Respond with ONLY the title, no additional text."""

    def build_structure_extraction_prompt(self, topic: str, title: str) -> str:
        """Generate a prompt for creating a structure outline."""
        return f"""You are creating a cheatsheet titled "{title}" about: {topic}

Generate a clear 6-point structure outline for this cheatsheet. Each point should be:
- A major concept or section heading
- Concise (3-10 words)
- Logically ordered from basics to advanced

Format as a numbered list (1. ... 2. ... etc).

Respond with ONLY the numbered list, no additional text."""

    def build_content_generation_prompt(self, topic: str, title: str, structure: str) -> str:
        """Generate a prompt for detailed content generation."""
        return f"""You are creating comprehensive cheatsheet content.

CHEATSHEET TITLE: {title}
TOPIC: {topic}

STRUCTURE TO FOLLOW:
{structure}

Generate detailed content for each section. For each section:
- Provide 3-5 key points
- Include practical examples where relevant
- Use clear, direct language
- Avoid copying from standard references — create original explanations
- Format each section with a header

Make the content educational, practical, and unique."""

    def build_image_analysis_prompt(self, image_description: str = "") -> str:
        """Generate a prompt for analyzing image content."""
        return f"""Analyze this image and extract key technical concepts. {image_description}

Create a cheatsheet structure based on what you see. Generate:
1. A concise title
2. 5-7 major topics/sections
3. Key points for each section

Focus on practical, actionable information."""


def create_prompt_builder() -> PromptBuilder:
    """Factory function to create and return a PromptBuilder instance."""
    return PromptBuilder()
