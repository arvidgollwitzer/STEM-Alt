"""Closed-API generators: GPT-4o, Claude 3.7 Sonnet, Gemini 2.5 Pro.

Each subclass logs the exact model version and the decoding parameters
so the run is auditable even if the upstream API drifts. Generation
calls retry on transient errors with exponential backoff.
"""

from __future__ import annotations

import base64
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from stem_alt.generator import register_generator
from stem_alt.generator.base import AltTextGenerator, GenerationResult
from stem_alt.generator.prompts import assemble_prompt


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _encode_image(image_path: str) -> str:
    return base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")


@register_generator("gpt4o")
class OpenAIGenerator(AltTextGenerator):
    """OpenAI GPT-4o (or compatible) multimodal generator."""

    def __init__(self, cfg: Any) -> None:
        super().__init__(cfg)
        from openai import OpenAI  # imported lazily to keep test deps slim

        self._client = OpenAI()

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def generate(
        self,
        image_path: str,
        context: str,
        prompt_name: str,
        previous_critique: Optional[str] = None,
        round_index: int = 0,
    ) -> GenerationResult:
        prompt_text = assemble_prompt(prompt_name, context, previous_critique)
        image_b64 = _encode_image(image_path)
        response = self._client.chat.completions.create(
            model=self.model_version,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
        )
        text = response.choices[0].message.content or ""
        return GenerationResult(
            figure_id=Path(image_path).stem,
            text=text,
            prompt_name=prompt_name,
            model_version=self.model_version,
            decoding_params=json.dumps({"temperature": self.temperature}),
            timestamp=_now(),
            round_index=round_index,
            critic_critique=previous_critique,
        )


@register_generator("claude")
class AnthropicGenerator(AltTextGenerator):
    """Anthropic Claude 3.7 Sonnet (or compatible)."""

    def __init__(self, cfg: Any) -> None:
        super().__init__(cfg)
        from anthropic import Anthropic

        self._client = Anthropic()

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def generate(
        self,
        image_path: str,
        context: str,
        prompt_name: str,
        previous_critique: Optional[str] = None,
        round_index: int = 0,
    ) -> GenerationResult:
        prompt_text = assemble_prompt(prompt_name, context, previous_critique)
        image_b64 = _encode_image(image_path)
        response = self._client.messages.create(
            model=self.model_version,
            max_tokens=getattr(self.cfg, "max_tokens", 1024),
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": prompt_text},
                    ],
                }
            ],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return GenerationResult(
            figure_id=Path(image_path).stem,
            text=text,
            prompt_name=prompt_name,
            model_version=self.model_version,
            decoding_params=json.dumps({"temperature": self.temperature}),
            timestamp=_now(),
            round_index=round_index,
            critic_critique=previous_critique,
        )


@register_generator("gemini")
class GeminiGenerator(AltTextGenerator):
    """Google Gemini 2.5 Pro (or compatible)."""

    def __init__(self, cfg: Any) -> None:
        super().__init__(cfg)
        import google.generativeai as genai

        self._genai = genai
        self._model = genai.GenerativeModel(self.model_version)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def generate(
        self,
        image_path: str,
        context: str,
        prompt_name: str,
        previous_critique: Optional[str] = None,
        round_index: int = 0,
    ) -> GenerationResult:
        from PIL import Image

        prompt_text = assemble_prompt(prompt_name, context, previous_critique)
        image = Image.open(image_path)
        response = self._model.generate_content(
            [prompt_text, image],
            generation_config={"temperature": self.temperature},
        )
        text = getattr(response, "text", "") or ""
        return GenerationResult(
            figure_id=Path(image_path).stem,
            text=text,
            prompt_name=prompt_name,
            model_version=self.model_version,
            decoding_params=json.dumps({"temperature": self.temperature}),
            timestamp=_now(),
            round_index=round_index,
            critic_critique=previous_critique,
        )
