"""Stage 4: DPO fine-tune the critic's LoRA adapters from human ratings.

Reads loop traces from stage 2 and ratings from stage 3. Emits a new LoRA
checkpoint under `outputs/<run>/dpo/round_NN/`. Updates the critic config
in place so stage 5 picks up the new adapter without manual editing.
"""

from __future__ import annotations

import json
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from stem_alt.corpus.stratification import assert_calibration_only
from stem_alt.critic.rubric import RubricScore
from stem_alt.human import HumanRatingProtocol
from stem_alt.loop.orchestrator import LoopRecord, LoopRound
from stem_alt.training import TrainerFactory
from stem_alt.training.preference_pairs import build_pairs
from stem_alt.utils import get_logger, set_seed

LOGGER = get_logger(__name__)


def _load_loop_records(loop_dir: Path) -> dict[str, LoopRecord]:
    records: dict[str, LoopRecord] = {}
    for path in sorted(loop_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rounds = []
        for r in payload["rounds"]:
            from stem_alt.generator.base import GenerationResult

            rounds.append(
                LoopRound(
                    round_index=r["round_index"],
                    generation=GenerationResult(**r["generation"]),
                    score=RubricScore(**r["score"]),
                )
            )
        records[payload["figure_id"]] = LoopRecord(
            figure_id=payload["figure_id"], rounds=rounds, converged=payload["converged"]
        )
    return records


def _load_metadata(corpus_manifest: Path) -> dict[str, dict[str, str]]:
    import csv

    meta: dict[str, dict[str, str]] = {}
    with corpus_manifest.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            meta[row["figure_id"]] = {
                "image_path": row["image_path"],
                "context": row["context_paragraph"],
                "diagram_type": row["diagram_type"],
            }
    return meta


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    set_seed(cfg.seed)
    loop_dir = Path(cfg.output_dir) / "loop_traces"
    ratings_path = Path(cfg.output_dir) / "ratings.jsonl"
    if not ratings_path.exists():
        raise FileNotFoundError(f"Expected human ratings at {ratings_path}.")

    # splits.json is the split authority; fine-tuning must never see a
    # held-out figure. Guard against any leak in the loop traces.
    splits = json.loads(Path(cfg.corpus.splits_path).read_text(encoding="utf-8"))
    if "calibration" not in splits:
        raise ValueError(f"{cfg.corpus.splits_path} is missing the 'calibration' key.")
    records = _load_loop_records(loop_dir)
    assert_calibration_only(list(records), splits["calibration"])

    # Attach the two-rater consensus (per-dimension mean), not an arbitrary
    # single rater, so no collected rating is silently discarded.
    proto = HumanRatingProtocol.load(ratings_path, out_dir=Path(cfg.output_dir))
    for figure_id, score in proto.consensus_scores().items():
        if figure_id in records:
            records[figure_id].human_score = score

    meta = _load_metadata(Path(cfg.corpus.manifest_path))
    pairs = build_pairs(
        records=list(records.values()),
        figure_metadata=meta,
        lambda_between=cfg.training.lambda_between,
    )
    LOGGER.info("Built %d preference pairs from %d figures.", len(pairs), len(records))

    trainer = TrainerFactory(cfg.training.name)(cfg.training)
    out_dir = Path(cfg.output_dir) / "dpo"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = trainer.fit(pairs=pairs, round_index=0, out_dir=out_dir)
    LOGGER.info("DPO artefact: %s", artifact.lora_path)

    # Point critic config at the new LoRA path for downstream stages.
    updated_critic = OmegaConf.create(dict(cfg.critic))
    updated_critic.lora_path = str(artifact.lora_path)
    (Path(cfg.output_dir) / "critic.lora.yaml").write_text(
        OmegaConf.to_yaml(updated_critic), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
