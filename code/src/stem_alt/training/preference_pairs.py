"""Build DPO preference pairs from human ratings.

In-figure pairs:  for each figure, every pair of candidates (i, j) becomes
                  (winner, loser) by H-score (mean of D1, D2, D3). Ties are
                  dropped. Self-pairs are excluded.

Between-round pairs: for each figure, later rounds are preferred over earlier
                   rounds when the human-rating delta exceeds `delta_min`.
                   Weighted by `lambda_between` in the loss aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

from stem_alt.loop.orchestrator import LoopRecord


@dataclass(frozen=True)
class PreferencePair:
    figure_id: str
    winner_text: str
    loser_text: str
    image_path: str
    context: str
    diagram_type: str
    pair_kind: str  # "in_figure" or "between_round"
    weight: float = 1.0


def build_pairs(
    records: Sequence[LoopRecord],
    figure_metadata: Dict[str, Dict[str, str]],
    delta_min: float = 0.5,
    lambda_between: float = 0.3,
) -> List[PreferencePair]:
    """Return preference pairs across all `records`.

    `figure_metadata` maps figure_id -> {"image_path": ..., "context": ...,
    "diagram_type": ...}. `delta_min` is the minimum H-score gap to consider
    a pair as a clear preference; tied or near-tied pairs are dropped.
    """
    pairs: List[PreferencePair] = []
    for record in records:
        if record.human_score is None:
            continue
        meta = figure_metadata[record.figure_id]
        # In-figure: compare each round's candidate using critic-aligned proxy.
        # Practical implementation expects multiple human-rated candidates per
        # figure; loops with k candidates yield C(k, 2) pairs.
        scored = [(rd.generation.text, rd.score.primary_mean()) for rd in record.rounds]
        scored.append((record.final_generation.text, record.human_score.primary_mean()))
        for (text_a, mean_a), (text_b, mean_b) in combinations(scored, 2):
            if abs(mean_a - mean_b) < delta_min:
                continue
            winner_text, loser_text = (
                (text_a, text_b) if mean_a > mean_b else (text_b, text_a)
            )
            pairs.append(
                PreferencePair(
                    figure_id=record.figure_id,
                    winner_text=winner_text,
                    loser_text=loser_text,
                    image_path=meta["image_path"],
                    context=meta["context"],
                    diagram_type=meta["diagram_type"],
                    pair_kind="in_figure",
                    weight=1.0,
                )
            )
        # Between-round augmentation: prefer later round over earlier when delta is real.
        for i, j in combinations(range(len(record.rounds)), 2):
            ri, rj = record.rounds[i], record.rounds[j]
            delta = rj.score.primary_mean() - ri.score.primary_mean()
            if abs(delta) < delta_min:
                continue
            winner_text = rj.generation.text if delta > 0 else ri.generation.text
            loser_text = ri.generation.text if delta > 0 else rj.generation.text
            pairs.append(
                PreferencePair(
                    figure_id=record.figure_id,
                    winner_text=winner_text,
                    loser_text=loser_text,
                    image_path=meta["image_path"],
                    context=meta["context"],
                    diagram_type=meta["diagram_type"],
                    pair_kind="between_round",
                    weight=lambda_between,
                )
            )
    return pairs


def split_pairs_by_kind(
    pairs: Sequence[PreferencePair],
) -> Tuple[List[PreferencePair], List[PreferencePair]]:
    in_figure = [p for p in pairs if p.pair_kind == "in_figure"]
    between_round = [p for p in pairs if p.pair_kind == "between_round"]
    return in_figure, between_round
