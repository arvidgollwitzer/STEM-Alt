"""Krippendorff's alpha under interval-scale assumptions.

Default to interval scale per paper Section 3.5 Assumption 3. Ordinal-scale
alpha is reported as a robustness check via `level_of_measurement="ordinal"`.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np


def krippendorff_alpha(
    annotations: Sequence[Sequence[float]],
    level_of_measurement: str = "interval",
) -> float:
    """Compute Krippendorff's alpha for a 2-D rater x item matrix.

    `annotations[i][j]` is rater i's score on item j. Missing values may
    be encoded as `np.nan`.
    """
    try:
        import krippendorff as kp
    except ImportError as e:
        raise ImportError(
            "The 'krippendorff' package is required. Install with `uv add krippendorff`."
        ) from e
    matrix = np.asarray(annotations, dtype=float)
    # The `krippendorff` package raises when the value domain collapses to a
    # single point (i.e. all raters agree on the same constant). Conventionally
    # α is undefined in that case; return NaN so callers can branch on it.
    finite = matrix[~np.isnan(matrix)]
    if finite.size == 0 or np.unique(finite).size <= 1:
        return float("nan")
    return float(kp.alpha(reliability_data=matrix, level_of_measurement=level_of_measurement))
