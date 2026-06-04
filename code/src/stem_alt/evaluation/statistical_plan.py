"""Frozen pre-registered statistical plan.

Edits to this file after corpus collection must be flagged as protocol
deviations and reported in the limitations section.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np

from stem_alt.critic.rubric import RubricScore
from stem_alt.evaluation.krippendorff import krippendorff_alpha


@dataclass(frozen=True)
class StatisticalPlan:
    """Pre-registered thresholds. Match the paper's Section 4 exactly."""

    primary_alpha_threshold: float = 0.70
    primary_sustained_rounds: int = 2
    inter_rater_alpha_floor: float = 0.60
    secondary_alpha_g1: float = 0.65
    secondary_alpha_g2: float = 0.55
    secondary_alpha_g3: float = 0.50
    bootstrap_resamples: int = 2000
    bootstrap_confidence: float = 0.95
    significance_level: float = 0.05

    def is_primary_sustained(self, alpha_history: Sequence[float]) -> bool:
        """True iff the last `primary_sustained_rounds` alphas all clear the threshold.

        The paper's stopping criterion (Section 4) is `α ≥ 0.70 sustained for
        two consecutive r`. A single crossing is not enough.
        """
        n = self.primary_sustained_rounds
        if len(alpha_history) < n:
            return False
        return all(a >= self.primary_alpha_threshold for a in alpha_history[-n:])


@dataclass(frozen=True)
class HeldOutEvaluation:
    krippendorff_alpha_primary: float
    krippendorff_alpha_d1: float
    krippendorff_alpha_d2: float
    krippendorff_alpha_d3: float
    krippendorff_alpha_d4: float
    krippendorff_alpha_d5: float
    mean_abs_delta_primary: float
    n_items: int


def evaluate_held_out(
    critic_scores: Sequence[RubricScore],
    human_scores: Sequence[RubricScore],
) -> HeldOutEvaluation:
    """Compute the primary outcome and per-dimension alphas on the held-out split."""
    if len(critic_scores) != len(human_scores):
        raise ValueError(
            f"Critic and human sequences must align: "
            f"{len(critic_scores)} vs {len(human_scores)}"
        )
    n = len(critic_scores)
    primary_c = [s.primary_mean() for s in critic_scores]
    primary_h = [s.primary_mean() for s in human_scores]
    alpha_primary = krippendorff_alpha([primary_c, primary_h])
    per_dim: Dict[str, float] = {}
    for dim_name in (
        "D1_factual_correctness",
        "D2_information_sufficiency",
        "D3_domain_accuracy",
        "D4_hallucination",
        "D5_conciseness",
    ):
        c_vals = [getattr(s, dim_name) for s in critic_scores]
        h_vals = [getattr(s, dim_name) for s in human_scores]
        per_dim[dim_name] = krippendorff_alpha([c_vals, h_vals])
    mean_abs_delta = float(np.mean(np.abs(np.array(primary_c) - np.array(primary_h))))
    return HeldOutEvaluation(
        krippendorff_alpha_primary=alpha_primary,
        krippendorff_alpha_d1=per_dim["D1_factual_correctness"],
        krippendorff_alpha_d2=per_dim["D2_information_sufficiency"],
        krippendorff_alpha_d3=per_dim["D3_domain_accuracy"],
        krippendorff_alpha_d4=per_dim["D4_hallucination"],
        krippendorff_alpha_d5=per_dim["D5_conciseness"],
        mean_abs_delta_primary=mean_abs_delta,
        n_items=n,
    )
