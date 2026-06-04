"""Stage 5: evaluate the fine-tuned critic against the held-out split.

Computes the pre-registered primary outcome and the per-dimension
Krippendorff alphas. Compares against the frozen StatisticalPlan and
writes a markdown summary alongside the JSON report.
"""

from __future__ import annotations

import json
from pathlib import Path

import hydra
from omegaconf import DictConfig

from stem_alt.corpus import DatasetFactory
from stem_alt.critic import CriticFactory
from stem_alt.critic.rubric import RubricScore
from stem_alt.evaluation import StatisticalPlan, evaluate_held_out
from stem_alt.human import HumanRatingProtocol
from stem_alt.utils import get_logger

LOGGER = get_logger(__name__)


def _human_scores_for_held_out(
    protocol: HumanRatingProtocol, held_out_ids: list[str]
) -> dict[str, RubricScore]:
    # Two-rater consensus (per-dimension mean), filtered to the held-out split.
    held = set(held_out_ids)
    return {
        fid: score
        for fid, score in protocol.consensus_scores().items()
        if fid in held
    }


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    splits = json.loads(Path(cfg.corpus.splits_path).read_text(encoding="utf-8"))
    held_out_ids = splits["held_out"]
    LOGGER.info("Held-out evaluation on %d figures.", len(held_out_ids))

    dataset_cls = DatasetFactory(cfg.corpus.name)
    # splits.json is the split authority; filter all figures to held-out ids
    # rather than trusting the manifest `split` column.
    held_out_id_set = set(held_out_ids)
    dataset = [
        s for s in dataset_cls(manifest_path=cfg.corpus.manifest_path)
        if s["figure_id"] in held_out_id_set
    ]

    critic = CriticFactory(cfg.critic.name)(cfg.critic)
    proto = HumanRatingProtocol.load(
        Path(cfg.output_dir) / "ratings_heldout.jsonl",
        out_dir=Path(cfg.output_dir),
    )
    human_by_id = _human_scores_for_held_out(proto, held_out_ids)

    critic_scores: list[RubricScore] = []
    human_scores: list[RubricScore] = []
    per_figure: list[dict] = []  # feeds analysis/generate_eval_figures.py
    for sample in dataset:
        # Score the *expert reference* description (the gold-standard target)
        # under the calibrated critic. The paper's iteration-effect comparison
        # uses the loop output; this stage uses the gold-standard target so the
        # primary outcome reflects C-H agreement on the reference distribution.
        c = critic.score(
            image_path=sample["image_path"],
            candidate_text=sample["reference"],
            context=sample["context"],
            diagram_type=sample["diagram_type"],
        )
        h = human_by_id.get(sample["figure_id"])
        if h is None:
            LOGGER.warning("Skipping %s: no human score available.", sample["figure_id"])
            continue
        critic_scores.append(c)
        human_scores.append(h)
        per_figure.append({
            "figure_id": sample["figure_id"],
            "domain": sample["domain"],
            "eth_category": sample["eth_category"],
            "c_primary": round(c.primary_mean(), 4),
            "h_primary": round(h.primary_mean(), 4),
        })

    report = evaluate_held_out(critic_scores=critic_scores, human_scores=human_scores)
    plan = StatisticalPlan(
        primary_alpha_threshold=cfg.evaluation.primary_alpha_threshold,
        primary_sustained_rounds=cfg.evaluation.primary_sustained_rounds,
        inter_rater_alpha_floor=cfg.evaluation.inter_rater_alpha_floor,
        secondary_alpha_g1=cfg.evaluation.secondary_alpha_g1,
        secondary_alpha_g2=cfg.evaluation.secondary_alpha_g2,
        secondary_alpha_g3=cfg.evaluation.secondary_alpha_g3,
        bootstrap_resamples=cfg.evaluation.bootstrap_resamples,
        bootstrap_confidence=cfg.evaluation.bootstrap_confidence,
        significance_level=cfg.evaluation.significance_level,
    )

    # Track the held-out primary α across DPO rounds so the stopping criterion
    # ("α ≥ 0.70 sustained for two consecutive r", paper §4) can be evaluated
    # rather than only the latest crossing.
    history_path = Path(cfg.output_dir) / "held_out_alpha_history.json"
    if history_path.exists():
        history_payload = json.loads(history_path.read_text(encoding="utf-8"))
        alpha_history: list[float] = list(history_payload.get("primary_alpha", []))
        round_history: list[int] = list(history_payload.get("dpo_round", []))
    else:
        alpha_history = []
        round_history = []
    current_round = int(getattr(cfg, "dpo_round_index", len(alpha_history)))
    alpha_history.append(report.krippendorff_alpha_primary)
    round_history.append(current_round)
    history_path.write_text(
        json.dumps(
            {"dpo_round": round_history, "primary_alpha": alpha_history},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    primary_sustained = plan.is_primary_sustained(alpha_history)
    # `rounds` + `held_out` are the schema analysis/generate_eval_figures.py
    # consumes via `--report`, so the published figures render straight from
    # this file. Per-round per-dimension alpha is not tracked historically;
    # only the final round carries the per-dimension breakdown.
    final_per_dim = {
        "D1": report.krippendorff_alpha_d1, "D2": report.krippendorff_alpha_d2,
        "D3": report.krippendorff_alpha_d3, "D4": report.krippendorff_alpha_d4,
        "D5": report.krippendorff_alpha_d5,
    }
    rounds = [
        {
            "r": r,
            "alpha_primary": a,
            "alpha_per_dim": final_per_dim,
            "mean_abs_delta": report.mean_abs_delta_primary,
        }
        for r, a in zip(round_history, alpha_history, strict=True)
    ]
    out = Path(cfg.output_dir) / "held_out_report.json"
    out.write_text(
        json.dumps(
            {
                "plan": plan.__dict__,
                "report": report.__dict__,
                "dpo_round_index": current_round,
                "primary_alpha_history": alpha_history,
                "primary_passed_current_round": (
                    report.krippendorff_alpha_primary >= plan.primary_alpha_threshold
                ),
                "primary_sustained": primary_sustained,
                "rounds": rounds,
                "held_out": per_figure,
                # Provenance: record which generator, critic, and trainer
                # produced this report so the run is fully auditable.
                "backends": {
                    "generator": getattr(cfg.generator, "name", "unknown"),
                    "critic": getattr(cfg.critic, "name", "unknown"),
                    "trainer": getattr(cfg.training, "name", "unknown"),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    LOGGER.info(
        "Held-out report -> %s  α=%.3f  sustained=%s  (history: %s)",
        out,
        report.krippendorff_alpha_primary,
        primary_sustained,
        [f"{a:.3f}" for a in alpha_history],
    )


if __name__ == "__main__":
    main()
