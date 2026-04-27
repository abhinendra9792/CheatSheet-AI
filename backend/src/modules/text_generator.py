"""
Text Generator Module — Step 1: Understand User (Text Input)
Uses Gemini via the NEW google-genai SDK with smart model fallback.

Model fallback chain: gemini-2.5-flash → gemini-2.5-pro → gemini-2.0-flash
Handles 429 rate limits automatically by trying next model in chain.
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from google import genai
from google.genai import types
from src.utils.logger import text_gen_logger
from config.settings import config


class TextGenerationError(Exception):
    """Exception raised for text generation errors"""
    pass


class TextGenerator:
    """
    Step 1: Understand user text input using Gemini.
    Has smart model fallback to handle rate limits on free tier.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TextGenerator with Gemini Pro API key (Step 1, 4, 5).
        Also creates fallback clients using Nano and Deep Research keys.
        """
        self.api_key = api_key or config.GEMINI_PRO_API_KEY
        self.logger = text_gen_logger
        self.model_chain = config.GEMINI_PRO_MODELS  # Fallback chain

        if not self.api_key:
            raise TextGenerationError(
                "GEMINI_PRO_API_KEY not configured. "
                "Set it in backend/.env (Step 1, 4, 5 key)."
            )

        # Primary client
        self.client = genai.Client(api_key=self.api_key)

        # Build list of (client, label) for multi-key fallback
        self.clients = [(self.client, "pro-key")]
        # Add Nano Banana key as fallback
        nano_key = config.GEMINI_NANO_API_KEY
        if nano_key and nano_key != self.api_key:
            self.clients.append((genai.Client(api_key=nano_key), "nano-key"))
        # Add Deep Research key as fallback
        dr_key = config.DEEP_RESEARCH_API_KEY
        if dr_key and dr_key != self.api_key:
            self.clients.append((genai.Client(api_key=dr_key), "research-key"))
        # Add Imagen key as fallback (can also do text gen)
        img_key = config.IMAGEN_API_KEY
        if img_key and img_key != self.api_key:
            self.clients.append((genai.Client(api_key=img_key), "imagen-key"))

        self.logger.info(
            f"TextGenerator initialized | models={self.model_chain} | "
            f"keys={[lbl for _, lbl in self.clients]} | SDK=google-genai"
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Core: generate_text with model fallback
    # ──────────────────────────────────────────────────────────────────────
    async def generate_text(
        self,
        prompt: str,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        timeout: int = None,
    ) -> str:
        """
        Generate text using Gemini API with automatic model AND key fallback.
        Tries: each API key × each model. If all hit 429, waits and retries.
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE
        top_p = top_p if top_p is not None else config.TOP_P
        max_tokens = max_tokens or config.MAX_OUTPUT_TOKENS
        timeout = timeout or config.TEXT_GENERATION_TIMEOUT

        gen_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
        )

        # Retry the entire model+key chain up to MAX_RETRIES times
        for retry in range(config.MAX_RETRIES):
            errors = []

            # Try each API key client
            for client, key_label in self.clients:
                # Try each model with this client
                for model_name in self.model_chain:
                    try:
                        self.logger.info(
                            f"[Attempt {retry+1}/{config.MAX_RETRIES}] "
                            f"key={key_label} model={model_name} | temp={temperature}"
                        )
                        print(f"   Trying: {key_label} → {model_name}...")

                        loop = asyncio.get_event_loop()
                        response = await asyncio.wait_for(
                            loop.run_in_executor(
                                None,
                                lambda c=client, m=model_name: c.models.generate_content(
                                    model=m,
                                    contents=prompt,
                                    config=gen_config,
                                ),
                            ),
                            timeout=timeout,
                        )

                        generated_text = response.text
                        self.logger.info(
                            f"✅ Generated {len(generated_text)} chars using {key_label}/{model_name}"
                        )
                        return generated_text

                    except asyncio.TimeoutError:
                        msg = f"{key_label}/{model_name}: timed out after {timeout}s"
                        self.logger.warning(msg)
                        errors.append(msg)
                        continue

                    except Exception as e:
                        error_str = str(e)
                        is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str

                        if is_rate_limit:
                            self.logger.warning(
                                f"⚠️ {key_label}/{model_name}: Rate limited (429). Trying next..."
                            )
                            errors.append(f"{key_label}/{model_name}: Rate limited")
                            await asyncio.sleep(2)
                            continue
                        else:
                            msg = f"{key_label}/{model_name}: {error_str[:100]}"
                            self.logger.warning(msg)
                            errors.append(msg)
                            continue

            # All keys+models failed in this cycle
            all_rate_limited = all("Rate limited" in e for e in errors)
            if all_rate_limited and retry < config.MAX_RETRIES - 1:
                wait = 30 * (retry + 1)
                print(f"   ⏳ All keys rate-limited. Waiting {wait}s before retry {retry+2}...")
                self.logger.info(f"All keys rate-limited. Waiting {wait}s before retry.")
                await asyncio.sleep(wait)
                continue
            elif retry < config.MAX_RETRIES - 1:
                wait = 5 * (retry + 1)
                self.logger.info(f"Retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue

        # All retries exhausted
        all_errors = " | ".join(errors[-6:])  # Show last 6 errors
        raise TextGenerationError(
            f"All models failed after {config.MAX_RETRIES} retries. Errors: {all_errors}"
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Step 1: Understand User Text Input
    # ──────────────────────────────────────────────────────────────────────
    async def understand_user_input(self, user_prompt: str) -> Dict[str, Any]:
        """
        Step 1 — Understand User: Analyze the user's text prompt and extract
        structured understanding.
        """
        analysis_prompt = f"""You are an expert content analyst. Analyze the following user request for a cheatsheet and extract structured information.

USER REQUEST: "{user_prompt}"

Provide your analysis as JSON with these exact keys:
{{
    "topic": "The main topic/subject",
    "subtopics": ["list", "of", "5-8", "key", "subtopics"],
    "difficulty": "beginner | intermediate | advanced",
    "audience": "Target audience description",
    "key_concepts": ["list", "of", "core", "concepts", "to", "cover"],
    "summary": "A 2-3 sentence summary of what the cheatsheet should cover",
    "suggested_title": "A catchy, professional title for the cheatsheet"
}}

Respond with ONLY valid JSON, no markdown formatting or code blocks."""

        self.logger.info(f"[Step 1] Understanding user input: {user_prompt[:80]}...")

        raw_text = await self.generate_text(analysis_prompt, temperature=0.3)
        parsed = self._extract_json(raw_text)

        self.logger.info(f"[Step 1] ✅ Understood topic: {parsed.get('topic', 'unknown')}")
        return parsed

    # ──────────────────────────────────────────────────────────────────────
    #  Retry wrapper
    # ──────────────────────────────────────────────────────────────────────
    async def generate_with_retry(
        self, prompt: str, max_retries: int = 3, **kwargs
    ) -> str:
        """Generate text with automatic retry and exponential backoff."""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries}")
                return await self.generate_text(prompt, **kwargs)
            except TextGenerationError as e:
                if attempt == max_retries - 1:
                    raise
                wait = config.RETRY_BASE_DELAY * (2 ** attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {wait}s: {e}"
                )
                await asyncio.sleep(wait)

    # ──────────────────────────────────────────────────────────────────────
    #  Structured content
    # ──────────────────────────────────────────────────────────────────────
    async def generate_structured_content(
        self, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        """Generate and parse JSON-structured content."""
        text = await self.generate_with_retry(prompt, **kwargs)
        return self._extract_json(text)

    # ──────────────────────────────────────────────────────────────────────
    #  JSON extraction helper
    # ──────────────────────────────────────────────────────────────────────
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract the first JSON object from a text response."""
        cleaned = text.strip()
        # Strip markdown code fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        start = cleaned.find("{")
        if start == -1:
            self.logger.warning("No JSON object found, returning raw text")
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
                        self.logger.warning("JSON parse failed, returning raw text")
                        return {"raw_response": text}

        return {"raw_response": text}
