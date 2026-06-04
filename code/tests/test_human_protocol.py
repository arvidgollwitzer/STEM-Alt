"""HumanRatingProtocol: JSONL round-trip, two-rater coverage, consensus.

Covers the stage-3 ingest path the smoke test bypasses (it injects scores
directly). A schema drift in the ratings JSONL would break the only path that
attaches real H-scores, so it is tested here explicitly.
"""

from __future__ import annotations

from pathlib import Path

from stem_alt.critic.rubric import RubricScore
from stem_alt.human import HumanRatingProtocol, RaterRole, RatingRecord


def _record(fid: str, rid: str, role: RaterRole, score: RubricScore) -> RatingRecord:
    return RatingRecord(
        figure_id=fid, rater_id=rid, rater_role=role, candidate_round=0,
        score=score, rendered_via_nvda=(role == RaterRole.SCREEN_READER_USER),
        timestamp="2026-01-01T00:00:00+00:00",
    )


def test_ratings_jsonl_round_trip(tmp_path: Path) -> None:
    proto = HumanRatingProtocol(out_dir=tmp_path)
    s1 = RubricScore(4, 4, 4, 5, 4, critique="expert")
    s2 = RubricScore(5, 4, 4, 5, 3, critique="sru")
    proto.add(_record("fig1", "expert_01", RaterRole.DOMAIN_EXPERT, s1))
    proto.add(_record("fig1", "sru_01", RaterRole.SCREEN_READER_USER, s2))
    path = proto.save()

    loaded = HumanRatingProtocol.load(path, out_dir=tmp_path)
    assert len(loaded.records) == 2
    by_role = {r.rater_role: r for r in loaded.records}
    assert by_role[RaterRole.DOMAIN_EXPERT].score == s1
    assert by_role[RaterRole.SCREEN_READER_USER].score == s2
    assert loaded.figures_with_two_raters() == ["fig1"]
    assert loaded.budget_used() == 1


def test_consensus_is_per_dimension_mean(tmp_path: Path) -> None:
    """Consensus must average both raters, not keep an arbitrary single one."""
    proto = HumanRatingProtocol(out_dir=tmp_path)
    proto.add(_record("fig1", "e", RaterRole.DOMAIN_EXPERT, RubricScore(2, 2, 2, 4, 4)))
    proto.add(_record("fig1", "s", RaterRole.SCREEN_READER_USER, RubricScore(4, 4, 4, 4, 2)))
    consensus = proto.consensus_scores()
    assert set(consensus) == {"fig1"}
    c = consensus["fig1"]
    # Per-dimension mean: D1 (2+4)/2=3, D5 (4+2)/2=3, D4 (4+4)/2=4.
    assert c.D1_factual_correctness == 3
    assert c.D5_conciseness == 3
    assert c.D4_hallucination == 4
    assert c.primary_mean() == 3.0  # not 2.0 (expert) or 4.0 (sru)


def test_consensus_single_rater_passthrough(tmp_path: Path) -> None:
    proto = HumanRatingProtocol(out_dir=tmp_path)
    proto.add(_record("fig1", "e", RaterRole.DOMAIN_EXPERT, RubricScore(5, 5, 5, 5, 5)))
    assert proto.consensus_scores()["fig1"].primary_mean() == 5.0


def test_consensus_half_tie_rounds_half_up(tmp_path: Path) -> None:
    """A .5 tie resolves half-up, not by Python's banker's rounding."""
    proto = HumanRatingProtocol(out_dir=tmp_path)
    proto.add(_record("f", "e", RaterRole.DOMAIN_EXPERT, RubricScore(3, 3, 3, 4, 4)))
    proto.add(_record("f", "s", RaterRole.SCREEN_READER_USER, RubricScore(4, 4, 4, 5, 5)))
    c = proto.consensus_scores()["f"]  # every dimension mean ends in .5
    # 3.5 -> 4 (banker's would also give 4); 4.5 -> 5 (banker's gives 4) catches it.
    assert c.D1_factual_correctness == 4
    assert c.D4_hallucination == 5
    assert c.D5_conciseness == 5
