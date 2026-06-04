"""LLaVA-Next-7B critic with rank-16 LoRA adapters.

Frozen base model. Only the LoRA adapters update between DPO rounds.
The critic emits five Likert scores plus a one-paragraph critique as
structured JSON, parsed defensively at the boundary.
"""

from __future__ import annotations

import json
import re
from typing import Any

from stem_alt.critic import register_critic
from stem_alt.critic.base import CriticBase
from stem_alt.critic.rubric import RubricDimension, RubricScore
from stem_alt.utils import get_logger

LOGGER = get_logger(__name__)


CRITIC_SYSTEM_PROMPT = """\
You are an alt-text quality critic for STEM figures. Score the candidate alt-text
on the five dimensions below. Return STRICT JSON.

Dimensions (each 1-5 Likert):
  D1_factual_correctness:        is the description correct about what is visible?
  D2_information_sufficiency:    does it carry enough information for a screen-reader
                                 user to reconstruct the figure's claim?
  D3_domain_accuracy:            are technical terms used correctly in the figure's
                                 scientific domain?
  D4_hallucination:              5 = no invented content; 1 = many fabricated claims.
  D5_conciseness:                follows DIAGRAM length guidance for the figure type?

Output JSON ONLY:
{
  "D1_factual_correctness": int,
  "D2_information_sufficiency": int,
  "D3_domain_accuracy": int,
  "D4_hallucination": int,
  "D5_conciseness": int,
  "critique": str
}
"""


@register_critic("llava_next_7b")
class LLaVANextCritic(CriticBase):
    """Open-weights critic: LLaVA-Next-7B base + LoRA adapters."""

    def __init__(self, cfg: Any) -> None:
        super().__init__(cfg)
        self.base_model_id = getattr(cfg, "base_model_id", "llava-hf/llava-v1.6-mistral-7b-hf")
        self.lora_path = getattr(cfg, "lora_path", None)
        self.max_new_tokens = getattr(cfg, "max_new_tokens", 512)
        self.device = getattr(cfg, "device", "cuda")

        import torch
        from transformers import AutoProcessor, LlavaNextForConditionalGeneration

        self._torch = torch
        self._processor = AutoProcessor.from_pretrained(self.base_model_id)
        model = LlavaNextForConditionalGeneration.from_pretrained(
            self.base_model_id,
            torch_dtype=torch.bfloat16,
        )
        if self.lora_path is not None:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, self.lora_path)
        self._model = model.to(self.device)
        self._model.eval()

    def score(
        self,
        image_path: str,
        candidate_text: str,
        context: str,
        diagram_type: str,
    ) -> RubricScore:
        from PIL import Image

        user_msg = (
            f"DIAGRAM type: {diagram_type}\n"
            f"Surrounding context:\n---\n{context}\n---\n"
            f"Candidate alt-text:\n---\n{candidate_text}\n---\n"
            "Return your rubric scores as strict JSON."
        )
        prompt = (
            f"<s>[INST] <<SYS>>\n{CRITIC_SYSTEM_PROMPT}\n<</SYS>>\n\n"
            f"<image>\n{user_msg} [/INST]"
        )
        image = Image.open(image_path).convert("RGB")
        inputs = self._processor(prompt, image, return_tensors="pt").to(self.device)
        with self._torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )
        raw = self._processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> RubricScore:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            LOGGER.warning("Critic emitted no JSON; falling back to mid-scale.")
            return RubricScore(3, 3, 3, 3, 3, critique="Parser fallback: no JSON")
        payload = json.loads(match.group(0))
        return RubricScore(
            D1_factual_correctness=int(payload[RubricDimension.D1_FACTUAL_CORRECTNESS.value]),
            D2_information_sufficiency=int(
                payload[RubricDimension.D2_INFORMATION_SUFFICIENCY.value]
            ),
            D3_domain_accuracy=int(payload[RubricDimension.D3_DOMAIN_ACCURACY.value]),
            D4_hallucination=int(payload[RubricDimension.D4_HALLUCINATION.value]),
            D5_conciseness=int(payload[RubricDimension.D5_CONCISENESS.value]),
            critique=str(payload.get("critique", "")),
        )
