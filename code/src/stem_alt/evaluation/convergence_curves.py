"""Bootstrap convergence curve: mean |C-H| versus DPO round."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class BootstrapCI:
    mean: float
    lower: float
    upper: float


def bootstrap_score_ci(
    deltas: Sequence[float],
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> BootstrapCI:
    """Figure-stratified bootstrap CI on mean |C-H| primary-outcome delta."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(deltas, dtype=float)
    if arr.size == 0:
        return BootstrapCI(float("nan"), float("nan"), float("nan"))
    means = np.empty(n_resamples, dtype=float)
    for b in range(n_resamples):
        sample = rng.choice(arr, size=arr.size, replace=True)
        means[b] = sample.mean()
    alpha = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(means, [alpha, 1.0 - alpha])
    return BootstrapCI(mean=float(arr.mean()), lower=float(lower), upper=float(upper))


def convergence_curve(
    deltas_by_round: Sequence[Sequence[float]],
    n_resamples: int = 2000,
    seed: int = 42,
) -> Sequence[Tuple[int, BootstrapCI]]:
    """Return (round_index, bootstrap CI) tuples for each DPO round."""
    return [
        (r, bootstrap_score_ci(deltas, n_resamples=n_resamples, seed=seed + r))
        for r, deltas in enumerate(deltas_by_round)
    ]
