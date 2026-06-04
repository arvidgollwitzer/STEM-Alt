"""Open-weights generator: LLaVA-Next-7B.

The fourth generator in the comparison family. Unlike the closed-API
generators it can be pinned at a model revision, so it anchors the
reproducible end of the generator spectrum. It loads the same base model
family as the critic but is used here only to draft alt-text, never to score.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional

from stem_alt.generator import register_generator
from stem_alt.generator.base import AltTextGenerator, GenerationResult
from stem_alt.generator.prompts import assemble_prompt


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


@register_generator("llava_next")
class LLaVANextGenerator(AltTextGenerator):
    """Open-weights LLaVA-Next-7B alt-text generator.

    `cfg` fields:
      base_model_id: HuggingFace model id (default llava-v1.6-mistral-7b-hf)
      model_version: revision/tag recorded for provenance
      device:        torch device (default "cuda")
      max_new_tokens: generation budget (default 512)
      temperature:   decoding temperature (default 0.0, greedy)
    """

    def __init__(self, cfg: Any) -> None:
        super().__init__(cfg)
        self.base_model_id = getattr(
            cfg, "base_model_id", "llava-hf/llava-v1.6-mistral-7b-hf"
        )
        self.device = getattr(cfg, "device", "cuda")
        self.max_new_tokens = getattr(cfg, "max_new_tokens", 512)

        import torch
        from transformers import AutoProcessor, LlavaNextForConditionalGeneration

        self._torch = torch
        self._processor = AutoProcessor.from_pretrained(self.base_model_id)
        model = LlavaNextForConditionalGeneration.from_pretrained(
            self.base_model_id,
            torch_dtype=torch.bfloat16,
        )
        self._model = model.to(self.device)
        self._model.eval()

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
        prompt = f"<s>[INST] <image>\n{prompt_text} [/INST]"
        image = Image.open(image_path).convert("RGB")
        inputs = self._processor(prompt, image, return_tensors="pt").to(self.device)
        do_sample = self.temperature > 0.0
        with self._torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=do_sample,
                temperature=self.temperature if do_sample else None,
            )
        decoded = self._processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        # Keep only the assistant turn after the instruction delimiter.
        text = decoded.split("[/INST]")[-1].strip()
        return GenerationResult(
            figure_id=Path(image_path).stem,
            text=text,
            prompt_name=prompt_name,
            model_version=self.model_version,
            decoding_params=json.dumps(
                {"temperature": self.temperature, "max_new_tokens": self.max_new_tokens}
            ),
            timestamp=_now(),
            round_index=round_index,
            critic_critique=previous_critique,
        )
