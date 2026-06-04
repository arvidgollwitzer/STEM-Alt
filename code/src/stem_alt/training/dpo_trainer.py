"""DPO trainer for the critic's LoRA adapters.

Thin wrapper around `trl.DPOTrainer` so the training loop slots into the
project pipeline. The reference policy is the frozen pre-DPO critic;
adapters are zero-initialised so r_C is well-defined at r=0 (Assumption 1
in paper Section 3.5).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Sequence

from stem_alt.training import register_trainer
from stem_alt.training.preference_pairs import PreferencePair
from stem_alt.utils import get_logger, set_seed

LOGGER = get_logger(__name__)


@dataclass
class DPOArtifact:
    """Path to the new LoRA checkpoint plus training-side metadata."""

    lora_path: Path
    round_index: int
    n_in_figure_pairs: int
    n_between_round_pairs: int
    beta: float


@register_trainer("dpo")
class DPOTrainer:
    """Direct Preference Optimization on the critic's LoRA adapters.

    `cfg` fields:
      base_model_id: HuggingFace model id (string)
      lora_r:        LoRA rank (int, default 16)
      lora_alpha:    LoRA alpha (int, default 32)
      lora_dropout:  LoRA dropout (float, default 0.05)
      beta:          DPO regularisation weight (float, default 0.1)
      lambda_between: weight for between-round pairs (float, default 0.3)
      lr:            learning rate (float, default 5e-5)
      epochs:        epochs per fine-tuning round (int, default 1)
      seed:          random seed (int, default 42)
    """

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.beta = getattr(cfg, "beta", 0.1)
        self.lambda_between = getattr(cfg, "lambda_between", 0.3)
        self.lr = getattr(cfg, "lr", 5e-5)
        self.epochs = getattr(cfg, "epochs", 1)
        self.seed = getattr(cfg, "seed", 42)

    def fit(
        self,
        pairs: Sequence[PreferencePair],
        round_index: int,
        out_dir: Path,
    ) -> DPOArtifact:
        """Run one DPO fine-tuning round against `pairs`."""
        set_seed(self.seed + round_index)
        in_figure_pairs = [p for p in pairs if p.pair_kind == "in_figure"]
        between_round_pairs = [p for p in pairs if p.pair_kind == "between_round"]
        LOGGER.info(
            "DPO r=%d  pairs: in_figure=%d  between_round=%d  beta=%.3f",
            round_index,
            len(in_figure_pairs),
            len(between_round_pairs),
            self.beta,
        )

        # The actual TRL call lives behind a guard so unit tests that don't
        # need GPU model loading can exercise this module's contract.
        from peft import LoraConfig
        from transformers import AutoTokenizer
        from trl import DPOConfig
        from trl import DPOTrainer as TRLDPOTrainer

        tokenizer = AutoTokenizer.from_pretrained(self.cfg.base_model_id)
        peft_config = LoraConfig(
            r=getattr(self.cfg, "lora_r", 16),
            lora_alpha=getattr(self.cfg, "lora_alpha", 32),
            lora_dropout=getattr(self.cfg, "lora_dropout", 0.05),
            target_modules=getattr(
                self.cfg,
                "lora_target_modules",
                ["q_proj", "k_proj", "v_proj", "o_proj"],
            ),
            bias="none",
            task_type="CAUSAL_LM",
        )
        dpo_cfg = DPOConfig(
            output_dir=str(out_dir / f"round_{round_index:02d}"),
            beta=self.beta,
            learning_rate=self.lr,
            num_train_epochs=self.epochs,
            per_device_train_batch_size=getattr(self.cfg, "per_device_batch", 1),
            gradient_accumulation_steps=getattr(self.cfg, "grad_accum", 8),
            logging_steps=10,
            save_strategy="epoch",
            seed=self.seed + round_index,
        )
        dataset = self._to_dataset(in_figure_pairs + between_round_pairs)
        # TRL renamed the `tokenizer` argument to `processing_class` in
        # v0.12; pass whichever the installed version accepts so the trainer
        # constructs across TRL releases.
        import inspect

        trainer_kwargs = dict(
            model=self.cfg.base_model_id,
            ref_model=None,  # reuse base policy via LoRA disable
            args=dpo_cfg,
            train_dataset=dataset,
            peft_config=peft_config,
        )
        if "processing_class" in inspect.signature(TRLDPOTrainer).parameters:
            trainer_kwargs["processing_class"] = tokenizer
        else:
            trainer_kwargs["tokenizer"] = tokenizer
        trainer = TRLDPOTrainer(**trainer_kwargs)
        trainer.train()
        ckpt = Path(str(dpo_cfg.output_dir))
        trainer.save_model(str(ckpt))
        return DPOArtifact(
            lora_path=ckpt,
            round_index=round_index,
            n_in_figure_pairs=len(in_figure_pairs),
            n_between_round_pairs=len(between_round_pairs),
            beta=self.beta,
        )

    @staticmethod
    def _to_dataset(pairs: Sequence[PreferencePair]):
        """Materialise pairs as a HuggingFace `datasets.Dataset`."""
        from datasets import Dataset

        rows: List[dict] = [
            {
                "prompt": _format_prompt(p),
                "chosen": p.winner_text,
                "rejected": p.loser_text,
                "weight": p.weight,
            }
            for p in pairs
        ]
        return Dataset.from_list(rows)


def _format_prompt(p: PreferencePair) -> str:
    return (
        f"DIAGRAM type: {p.diagram_type}\n"
        f"Context:\n---\n{p.context}\n---\n"
        f"Score this alt-text on the 5-dimension rubric."
    )
