"""Preference-pair construction from loop traces + human ratings."""

from __future__ import annotations

from stem_alt.critic.rubric import RubricScore
from stem_alt.generator.base import GenerationResult
from stem_alt.loop.orchestrator import LoopRecord, LoopRound
from stem_alt.training.preference_pairs import build_pairs, split_pairs_by_kind


def _gen(text: str, idx: int) -> GenerationResult:
    return GenerationResult(
        figure_id="fig1",
        text=text,
        prompt_name="P2",
        model_version="gpt-4o-2024-11-20",
        decoding_params="{\"temperature\": 0.0}",
        timestamp="2026-04-01T00:00:00Z",
        round_index=idx,
    )


def _round(text: str, idx: int, score_primary: int) -> LoopRound:
    return LoopRound(
        round_index=idx,
        generation=_gen(text, idx),
        score=RubricScore(score_primary, score_primary, score_primary, 3, 3),
    )


def test_in_figure_pairs_built_from_score_gaps() -> None:
    record = LoopRecord(
        figure_id="fig1",
        rounds=[_round("low", 0, 2), _round("high", 1, 4)],
        human_score=RubricScore(5, 5, 5, 5, 4),
    )
    meta = {"fig1": {"image_path": "img.png", "context": "ctx", "diagram_type": "Graph"}}
    pairs = build_pairs(records=[record], figure_metadata=meta, delta_min=0.5)
    in_fig, between = split_pairs_by_kind(pairs)
    assert in_fig, "Expected at least one in-figure pair from clear score gap."
    assert all(p.weight == 1.0 for p in in_fig)
    assert all(p.weight == 0.3 for p in between)


def test_ties_dropped_when_below_delta_min() -> None:
    record = LoopRecord(
        figure_id="fig1",
        rounds=[_round("a", 0, 3), _round("b", 1, 3)],
        human_score=RubricScore(3, 3, 3, 3, 3),
    )
    meta = {"fig1": {"image_path": "img.png", "context": "ctx", "diagram_type": "Graph"}}
    pairs = build_pairs(records=[record], figure_metadata=meta, delta_min=0.5)
    assert pairs == []


def test_pair_counts_exact() -> None:
    """Lock the C(k,2) arithmetic so a regression in pair generation fails.

    Two rounds (primary 2, 4) plus the human candidate (primary 5) give three
    scored candidates with all-distinct means -> C(3,2)=3 in-figure pairs.
    The two rounds differ by 2 (>= delta_min) -> 1 between-round pair.
    """
    record = LoopRecord(
        figure_id="fig1",
        rounds=[_round("low", 0, 2), _round("high", 1, 4)],
        human_score=RubricScore(5, 5, 5, 5, 4),
    )
    meta = {"fig1": {"image_path": "img.png", "context": "ctx", "diagram_type": "Graph"}}
    in_fig, between = split_pairs_by_kind(
        build_pairs(records=[record], figure_metadata=meta, delta_min=0.5)
    )
    assert len(in_fig) == 3
    assert len(between) == 1
