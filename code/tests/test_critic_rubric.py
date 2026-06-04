"""RubricScore validation + primary outcome arithmetic."""

from __future__ import annotations

import pytest

from stem_alt.critic.rubric import RubricScore


def test_primary_mean() -> None:
    s = RubricScore(4, 4, 5, 3, 4)
    assert s.primary_mean() == pytest.approx((4 + 4 + 5) / 3.0)


def test_rejects_out_of_scale_values() -> None:
    with pytest.raises(ValueError):
        RubricScore(0, 3, 3, 3, 3)
    with pytest.raises(ValueError):
        RubricScore(3, 3, 6, 3, 3)


def test_as_dict_round_trip() -> None:
    s = RubricScore(2, 3, 4, 5, 1, critique="terse")
    d = s.as_dict()
    assert d["D1_factual_correctness"] == 2
    assert d["critique"] == "terse"
