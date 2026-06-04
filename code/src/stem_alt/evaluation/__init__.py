"""Evaluation module: pre-registered statistical plan + held-out metrics."""

from __future__ import annotations

from .convergence_curves import bootstrap_score_ci, convergence_curve
from .krippendorff import krippendorff_alpha
from .statistical_plan import StatisticalPlan, evaluate_held_out

__all__ = [
    "krippendorff_alpha",
    "convergence_curve",
    "bootstrap_score_ci",
    "StatisticalPlan",
    "evaluate_held_out",
]
