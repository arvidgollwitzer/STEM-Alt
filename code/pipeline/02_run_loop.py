"""Stage 2: run the G-C loop across the calibration split.

Per-figure trace persisted as JSON. The trace is the input to stage 3
(human rating) and stage 4 (DPO fine-tuning).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import hydra
from omegaconf import DictConfig

from stem_alt.corpus import DatasetFactory
from stem_alt.critic import CriticFactory
from stem_alt.generator import GeneratorFactory
from stem_alt.loop import ConvergenceCheck, LoopOrchestrator
from stem_alt.utils import get_logger, set_seed

LOGGER = get_logger(__name__)


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    set_seed(cfg.seed)
    # splits.json (written by stage 1) is the single split authority; the
    # manifest `split` column is informational. Iterate the calibration ids.
    splits = json.loads(Path(cfg.corpus.splits_path).read_text(encoding="utf-8"))
    calibration_ids = set(splits["calibration"])
    dataset_cls = DatasetFactory(cfg.corpus.name)
    dataset = dataset_cls(manifest_path=cfg.corpus.manifest_path)
    LOGGER.info("Loop on calibration split: %d figures", len(calibration_ids))

    generator = GeneratorFactory(cfg.generator.name)(cfg.generator)
    critic = CriticFactory(cfg.critic.name)(cfg.critic)
    orchestrator = LoopOrchestrator(
        generator=generator,
        critic=critic,
        max_rounds=cfg.loop.max_rounds,
        convergence=ConvergenceCheck(
            epsilon=cfg.loop.convergence.epsilon,
            min_rounds=cfg.loop.convergence.min_rounds,
        ),
    )

    out_dir = Path(cfg.output_dir) / "loop_traces"
    out_dir.mkdir(parents=True, exist_ok=True)

    for sample in dataset:
        if sample["figure_id"] not in calibration_ids:
            continue
        record = orchestrator.run_for_figure(
            figure_id=sample["figure_id"],
            image_path=sample["image_path"],
            context=sample["context"],
            diagram_type=sample["diagram_type"],
            prompt_name=cfg.loop.prompt_name,
        )
        path = out_dir / f"{sample['figure_id']}.json"
        path.write_text(_serialise(record) + "\n", encoding="utf-8")
        LOGGER.info(
            "figure=%s rounds=%d converged=%s final_primary=%.3f",
            sample["figure_id"],
            len(record.rounds),
            record.converged,
            record.final_score.primary_mean(),
        )


def _serialise(record) -> str:
    payload = {
        "figure_id": record.figure_id,
        "converged": record.converged,
        "rounds": [
            {
                "round_index": rd.round_index,
                "generation": asdict(rd.generation),
                "score": rd.score.as_dict(),
            }
            for rd in record.rounds
        ],
    }
    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    main()
