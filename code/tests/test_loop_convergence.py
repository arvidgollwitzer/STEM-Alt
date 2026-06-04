"""ConvergenceCheck plateau detection and D4 hallucination guard."""

from __future__ import annotations

from dataclasses import dataclass

from stem_alt.critic.base import CriticBase
from stem_alt.critic.rubric import RubricScore
from stem_alt.generator.base import AltTextGenerator, GenerationResult
from stem_alt.loop import ConvergenceCheck
from stem_alt.loop.orchestrator import LoopOrchestrator


def test_not_converged_before_min_rounds() -> None:
    check = ConvergenceCheck(epsilon=0.1, min_rounds=2)
    assert not check.has_converged([3.0])
    assert not check.has_converged([3.0, 3.0])


def test_converges_when_delta_below_epsilon() -> None:
    check = ConvergenceCheck(epsilon=0.1, min_rounds=2)
    assert check.has_converged([2.0, 3.0, 3.05])


def test_does_not_converge_on_large_delta() -> None:
    check = ConvergenceCheck(epsilon=0.1, min_rounds=2)
    assert not check.has_converged([2.0, 3.0, 4.0])


@dataclass
class _StubGenerator(AltTextGenerator):
    """Deterministic stub that returns canned alt-text per round."""

    candidates: list[str]

    def generate(
        self,
        image_path: str,
        context: str,
        prompt_name: str,
        previous_critique: str | None = None,
        round_index: int = 0,
    ) -> GenerationResult:
        text = self.candidates[min(round_index, len(self.candidates) - 1)]
        return GenerationResult(
            figure_id="stub",
            text=text,
            prompt_name=prompt_name,
            model_version="stub",
            decoding_params="temperature=0",
            timestamp="2026-05-25T00:00:00Z",
            round_index=round_index,
            critic_critique=previous_critique,
        )


@dataclass
class _StubCritic(CriticBase):
    """Deterministic stub that returns canned RubricScores per round."""

    scores: list[RubricScore]
    calls: int = 0

    def score(
        self,
        image_path: str,
        candidate_text: str,
        context: str,
        diagram_type: str,
    ) -> RubricScore:
        s = self.scores[min(self.calls, len(self.scores) - 1)]
        self.calls += 1
        return s


def test_d4_below_threshold_flags_rejection_and_forces_revision() -> None:
    """Paper §5 mitigation: D4 <= threshold flags the round for rejection."""
    bad = RubricScore(
        D1_factual_correctness=3,
        D2_information_sufficiency=3,
        D3_domain_accuracy=3,
        D4_hallucination=1,
        D5_conciseness=3,
        critique="invented detail",
    )
    good = RubricScore(
        D1_factual_correctness=4,
        D2_information_sufficiency=4,
        D3_domain_accuracy=4,
        D4_hallucination=5,
        D5_conciseness=4,
        critique="clean",
    )
    gen = _StubGenerator(candidates=["bad", "fixed", "fixed", "fixed", "fixed"])
    crit = _StubCritic(scores=[bad, good, good, good, good])
    orch = LoopOrchestrator(
        generator=gen,
        critic=crit,
        max_rounds=5,
        hallucination_reject_threshold=2,
    )
    record = orch.run_for_figure(
        figure_id="t1",
        image_path="/tmp/x.png",
        context="ctx",
        diagram_type="Photos",
    )
    assert record.rounds[0].rejected_for_hallucination is True
    assert record.rounds[1].rejected_for_hallucination is False


def test_rejection_forces_revision_critique() -> None:
    """A D4 rejection must inject a 'remove fabricated content' critique next round."""
    bad = RubricScore(
        D1_factual_correctness=3, D2_information_sufficiency=3, D3_domain_accuracy=3,
        D4_hallucination=1, D5_conciseness=3, critique="invented detail",
    )
    good = RubricScore(
        D1_factual_correctness=4, D2_information_sufficiency=4, D3_domain_accuracy=4,
        D4_hallucination=5, D5_conciseness=4, critique="clean",
    )
    gen = _StubGenerator(candidates=["bad", "fixed", "fixed", "fixed", "fixed"])
    crit = _StubCritic(scores=[bad, good, good, good, good])
    orch = LoopOrchestrator(
        generator=gen, critic=crit, max_rounds=5, hallucination_reject_threshold=2
    )
    record = orch.run_for_figure(
        figure_id="t3", image_path="/tmp/z.png", context="ctx", diagram_type="Photos",
    )
    # Round 1's generation was produced from the forced-revision critique.
    round1_critique = record.rounds[1].generation.critic_critique
    assert round1_critique is not None
    assert "D4=" in round1_critique
    assert "Remove any claim not visible" in round1_critique


def test_d4_above_threshold_does_not_flag() -> None:
    clean = RubricScore(
        D1_factual_correctness=4,
        D2_information_sufficiency=4,
        D3_domain_accuracy=4,
        D4_hallucination=4,
        D5_conciseness=4,
        critique="ok",
    )
    gen = _StubGenerator(candidates=["a", "b", "c", "d", "e"])
    crit = _StubCritic(scores=[clean] * 5)
    orch = LoopOrchestrator(
        generator=gen,
        critic=crit,
        max_rounds=3,
        hallucination_reject_threshold=2,
    )
    record = orch.run_for_figure(
        figure_id="t2",
        image_path="/tmp/y.png",
        context="ctx",
        diagram_type="Photos",
    )
    assert all(not r.rejected_for_hallucination for r in record.rounds)
