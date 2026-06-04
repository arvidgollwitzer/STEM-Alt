"""Human rating protocol. Defines the rater roles and the rating record."""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

from stem_alt.critic.rubric import RubricScore


def _round_half_up(value: float) -> int:
    """Round to nearest integer, ties going up (3.5 -> 4, 4.5 -> 5).

    Python's built-in round() is banker's rounding (round-half-to-even:
    2.5 -> 2, 4.5 -> 4), which would bias a two-rater Likert consensus toward
    even integers. Half-up is the conventional, documented rule for the rubric.
    """
    import math

    return int(math.floor(value + 0.5))


class RaterRole(str, Enum):
    DOMAIN_EXPERT = "domain_expert"
    SCREEN_READER_USER = "screen_reader_user"
    SIGHTED_FALLBACK = "sighted_fallback_with_sr_experience"


@dataclass(frozen=True)
class RatingRecord:
    """One human rating attached to one (figure, candidate) pair."""

    figure_id: str
    rater_id: str
    rater_role: RaterRole
    candidate_round: int
    score: RubricScore
    rendered_via_nvda: bool
    timestamp: str


@dataclass
class HumanRatingProtocol:
    """Track ratings, enforce two-rater coverage, and expose budget telemetry."""

    out_dir: Path
    records: List[RatingRecord] = field(default_factory=list)

    def add(self, record: RatingRecord) -> None:
        self.records.append(record)

    def figures_with_two_raters(self) -> List[str]:
        counts: Dict[str, set] = {}
        for r in self.records:
            counts.setdefault(r.figure_id, set()).add(r.rater_role)
        required = {RaterRole.DOMAIN_EXPERT, RaterRole.SCREEN_READER_USER}
        return sorted(fid for fid, roles in counts.items() if required.issubset(roles))

    def budget_used(self) -> int:
        return len(self.figures_with_two_raters())

    def consensus_scores(self) -> Dict[str, RubricScore]:
        """Per-figure consensus rubric score across that figure's raters.

        The protocol records two raters per figure (a domain expert and a
        screen-reader user). The consensus is the per-dimension mean across
        all raters of the figure, rounded to the nearest integer so it stays
        a valid 1-5 RubricScore. Ties (means ending in .5) round up by the
        documented half-up rule, not Python's banker's rounding. Downstream
        stages (DPO pair construction, held-out evaluation) must use this rather
        than an arbitrary single rater, otherwise half the collected ratings are
        silently discarded.
        """
        from collections import defaultdict

        buckets: Dict[str, List[RubricScore]] = defaultdict(list)
        for record in self.records:
            buckets[record.figure_id].append(record.score)

        consensus: Dict[str, RubricScore] = {}
        for figure_id, scores in buckets.items():
            n = len(scores)

            def _mean(attr: str, _scores: List[RubricScore] = scores) -> int:
                return _round_half_up(sum(getattr(s, attr) for s in _scores) / len(_scores))

            consensus[figure_id] = RubricScore(
                D1_factual_correctness=_mean("D1_factual_correctness"),
                D2_information_sufficiency=_mean("D2_information_sufficiency"),
                D3_domain_accuracy=_mean("D3_domain_accuracy"),
                D4_hallucination=_mean("D4_hallucination"),
                D5_conciseness=_mean("D5_conciseness"),
                critique=f"Consensus of {n} rater(s).",
            )
        return consensus

    def save(self) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / f"ratings_{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for r in self.records:
                payload = {
                    "figure_id": r.figure_id,
                    "rater_id": r.rater_id,
                    "rater_role": r.rater_role.value,
                    "candidate_round": r.candidate_round,
                    "score": r.score.as_dict(),
                    "rendered_via_nvda": r.rendered_via_nvda,
                    "timestamp": r.timestamp,
                }
                fh.write(json.dumps(payload) + "\n")
        return path

    @classmethod
    def load(cls, jsonl_path: Path, out_dir: Path) -> "HumanRatingProtocol":
        proto = cls(out_dir=out_dir)
        with jsonl_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                payload = json.loads(line)
                score = RubricScore(**payload["score"])
                proto.records.append(
                    RatingRecord(
                        figure_id=payload["figure_id"],
                        rater_id=payload["rater_id"],
                        rater_role=RaterRole(payload["rater_role"]),
                        candidate_round=int(payload["candidate_round"]),
                        score=score,
                        rendered_via_nvda=bool(payload["rendered_via_nvda"]),
                        timestamp=payload["timestamp"],
                    )
                )
        return proto
