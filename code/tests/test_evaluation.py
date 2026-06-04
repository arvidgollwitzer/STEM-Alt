"""Held-out evaluation + bootstrap CI."""

from __future__ import annotations

import math

from stem_alt.critic.rubric import RubricScore
from stem_alt.evaluation import StatisticalPlan, bootstrap_score_ci, evaluate_held_out


def test_bootstrap_ci_brackets_the_mean() -> None:
    deltas = [0.2, 0.3, 0.25, 0.4, 0.35]
    ci = bootstrap_score_ci(deltas, n_resamples=500, seed=1)
    assert ci.lower <= ci.mean <= ci.upper


def test_perfect_agreement_yields_high_alpha() -> None:
    c = [RubricScore(5, 5, 5, 4, 4) for _ in range(10)]
    h = [RubricScore(5, 5, 5, 4, 4) for _ in range(10)]
    out = evaluate_held_out(c, h)
    assert out.mean_abs_delta_primary == 0.0
    # alpha for identical sequences is conventionally 1.0 (or NaN if no variance);
    # accept either, since krippendorff handles degenerate cases.
    assert math.isnan(out.krippendorff_alpha_primary) or out.krippendorff_alpha_primary > 0.99


def test_disagreement_lowers_alpha() -> None:
    c = [RubricScore(1, 1, 1, 1, 1), RubricScore(5, 5, 5, 5, 5)]
    h = [RubricScore(5, 5, 5, 5, 5), RubricScore(1, 1, 1, 1, 1)]
    out = evaluate_held_out(c, h)
    assert out.krippendorff_alpha_primary < 0.0
    assert out.mean_abs_delta_primary == 4.0


def test_sustained_requires_two_consecutive_crossings() -> None:
    plan = StatisticalPlan()  # threshold=0.70, sustained=2
    # Single crossing is not enough.
    assert plan.is_primary_sustained([0.55, 0.72]) is False
    # Two consecutive crossings clears the criterion.
    assert plan.is_primary_sustained([0.55, 0.72, 0.74]) is True
    # A dip after one crossing breaks sustained status.
    assert plan.is_primary_sustained([0.72, 0.65]) is False
    # Empty / under-length histories fail safe.
    assert plan.is_primary_sustained([]) is False
    assert plan.is_primary_sustained([0.99]) is False


def test_sustained_threshold_boundary_is_inclusive() -> None:
    plan = StatisticalPlan(primary_alpha_threshold=0.70, primary_sustained_rounds=2)
    # Exactly at the threshold counts as a crossing.
    assert plan.is_primary_sustained([0.70, 0.70]) is True
    # Just below does not.
    assert plan.is_primary_sustained([0.70, 0.6999]) is False
