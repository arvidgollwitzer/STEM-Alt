"""Plateau detection for the inner G-C loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ConvergenceCheck:
    """Stop the inner loop when the primary-outcome delta falls below `epsilon`.

    `epsilon` defaults to 0.1 on the 5-point primary-outcome scale, matching
    the paper's plateau definition.
    """

    epsilon: float = 0.1
    min_rounds: int = 2

    def has_converged(self, primary_outcome_history: List[float]) -> bool:
        if len(primary_outcome_history) < self.min_rounds + 1:
            return False
        prev = primary_outcome_history[-2]
        curr = primary_outcome_history[-1]
        return abs(curr - prev) < self.epsilon
