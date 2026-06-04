"""Stratified split across STEM domain x ETH alt-text category.

The held-out evaluation split is frozen at corpus build time. Stratification
preserves the 4 x 4 cell counts published in Table 1 of the paper.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from stem_alt.corpus.dataset import StemFigure

CalibrationSplit = List[str]
HeldOutSplit = List[str]


def stratified_split(
    figures: Sequence[StemFigure],
    held_out_target_per_cell: Dict[Tuple[str, str], int],
    seed: int = 42,
) -> Tuple[CalibrationSplit, HeldOutSplit]:
    """Partition `figures` by (domain, eth_category) cells.

    `held_out_target_per_cell` maps (domain, eth_category) -> number of
    figures to reserve for the held-out split. The remaining figures go
    to the calibration split.

    Raises `ValueError` if any cell has fewer figures than its target.
    """
    rng = random.Random(seed)
    by_cell: Dict[Tuple[str, str], List[StemFigure]] = defaultdict(list)
    for fig in figures:
        by_cell[(fig.domain, fig.eth_category.value)].append(fig)

    held_out: List[str] = []
    calibration: List[str] = []
    for cell, target in held_out_target_per_cell.items():
        bucket = by_cell.get(cell, [])
        if len(bucket) < target:
            raise ValueError(
                f"Cell {cell} has {len(bucket)} figures, target is {target}"
            )
        rng.shuffle(bucket)
        held_out.extend(f.figure_id for f in bucket[:target])
        calibration.extend(f.figure_id for f in bucket[target:])

    return sorted(calibration), sorted(held_out)


def assert_calibration_only(
    figure_ids: Sequence[str], calibration_ids: Sequence[str]
) -> None:
    """Raise if any `figure_ids` is not in the calibration split.

    The held-out split is frozen at corpus build time; fine-tuning must never
    see a held-out figure. Stage 4 calls this on the loop-trace figure ids
    before building preference pairs so a leak fails loud instead of silently
    contaminating the evaluation.
    """
    calibration = set(calibration_ids)
    if not calibration:
        raise ValueError("Calibration split is empty; refusing to build DPO pairs.")
    leaked = sorted(fid for fid in figure_ids if fid not in calibration)
    if leaked:
        raise ValueError(
            f"Loop traces contain non-calibration figures (held-out leak): {leaked}"
        )


def save_splits(
    calibration: CalibrationSplit,
    held_out: HeldOutSplit,
    out_path: Path,
) -> None:
    """Persist splits with provenance metadata."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "calibration": calibration,
                "held_out": held_out,
                "n_calibration": len(calibration),
                "n_held_out": len(held_out),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
