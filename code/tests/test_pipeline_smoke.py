"""End-to-end pipeline wiring test using in-process stubs.

Exercises every stage of the loop in-process: dataset load, stratified split,
G-C loop, human-rating injection (consensus), preference-pair build, DPO-round
artefact contract, held-out evaluation, and release-HTML WCAG validation.

The generator, critic, and trainer here are lightweight stubs defined in this file,
not the shipped backends. The shipped backends (OpenAI/Anthropic/Gemini/LLaVA
generators, the LLaVA-Next critic, the TRL DPO trainer) require API keys and a
GPU and are exercised against real models, not in CI. This test proves the
pipeline wiring and the cross-stage data contracts hold; it produces no
research results. The tiny fixture corpus is test data, used only here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from stem_alt.compliance import ETHCategory, WCAGValidator
from stem_alt.compliance.wcag_validator import FigureRecord
from stem_alt.corpus import DatasetFactory
from stem_alt.corpus.stratification import assert_calibration_only, stratified_split
from stem_alt.critic.base import CriticBase
from stem_alt.critic.rubric import SCALE_MAX, SCALE_MIN, RubricScore
from stem_alt.evaluation import evaluate_held_out
from stem_alt.generator.base import AltTextGenerator, GenerationResult
from stem_alt.loop import ConvergenceCheck, LoopOrchestrator
from stem_alt.training.dpo_trainer import DPOArtifact
from stem_alt.training.preference_pairs import PreferencePair, build_pairs

FIXTURE = Path(__file__).parent / "fixtures" / "tiny_corpus" / "manifest.csv"


def _clamp(value: int) -> int:
    return max(SCALE_MIN, min(SCALE_MAX, value))


class _StubGenerator(AltTextGenerator):
    """Deterministic stub: drafts lengthen across rounds."""

    def __init__(self) -> None:
        self.model_version = "stub-v0"
        self.temperature = 0.0

    def generate(
        self,
        image_path: str,
        context: str,
        prompt_name: str,
        previous_critique: Optional[str] = None,
        round_index: int = 0,
    ) -> GenerationResult:
        detail = " ".join(f"detail{i}" for i in range(round_index + 1))
        text = f"Alt-text for {Path(image_path).stem} (round {round_index}). {detail}."
        if previous_critique:
            text += " Addressed prior critique."
        return GenerationResult(
            figure_id=Path(image_path).stem,
            text=text,
            prompt_name=prompt_name,
            model_version=self.model_version,
            decoding_params=json.dumps({"temperature": 0.0}),
            timestamp="2026-01-01T00:00:00+00:00",
            round_index=round_index,
            critic_critique=previous_critique,
        )


class _StubCritic(CriticBase):
    """Deterministic stub: scores rise with draft length, then plateau."""

    def __init__(self) -> None:
        self.cfg = None

    def score(
        self,
        image_path: str,
        candidate_text: str,
        context: str,
        diagram_type: str,
    ) -> RubricScore:
        words = len(candidate_text.split())
        base = _clamp(2 + words // 8)
        addressed = "Addressed prior critique" in candidate_text
        return RubricScore(
            D1_factual_correctness=_clamp(base),
            D2_information_sufficiency=_clamp(base + (1 if addressed else 0)),
            D3_domain_accuracy=_clamp(base),
            D4_hallucination=_clamp(base + 1),
            D5_conciseness=_clamp(SCALE_MAX - max(0, words // 20)),
            critique=f"{words} words, addressed={addressed}.",
        )


class _StubTrainer:
    """Stub for the DPO trainer: writes an adapter dir, trains nothing."""

    def fit(
        self, pairs: Sequence[PreferencePair], round_index: int, out_dir: Path
    ) -> DPOArtifact:
        in_figure = [p for p in pairs if p.pair_kind == "in_figure"]
        between = [p for p in pairs if p.pair_kind == "between_round"]
        ckpt = out_dir / f"round_{round_index:02d}"
        ckpt.mkdir(parents=True, exist_ok=True)
        (ckpt / "adapter_config.json").write_text("{}\n", encoding="utf-8")
        return DPOArtifact(
            lora_path=ckpt,
            round_index=round_index,
            n_in_figure_pairs=len(in_figure),
            n_between_round_pairs=len(between),
            beta=0.1,
        )


def _human_score(seed: int) -> RubricScore:
    v = 3 + seed % 3
    return RubricScore(v, v, v, 5, 4, critique="injected")


def test_full_pipeline_wiring(tmp_path: Path) -> None:
    # Stage 1: load + stratified split.
    dataset = DatasetFactory("stem_alt")(manifest_path=str(FIXTURE))
    assert len(dataset) == 8
    target = {
        ("chemistry", "simple"): 1, ("chemistry", "complex"): 1,
        ("physics", "simple"): 1, ("physics", "complex"): 1,
    }
    calibration, held_out = stratified_split(dataset.figures, target, seed=42)
    assert len(calibration) == 4 and len(held_out) == 4
    cal_set, ho_set = set(calibration), set(held_out)

    orch = LoopOrchestrator(
        generator=_StubGenerator(), critic=_StubCritic(), max_rounds=5,
        convergence=ConvergenceCheck(epsilon=0.1, min_rounds=2),
    )

    # Stage 2 + 3: loop over calibration figures, attach injected human scores.
    by_id = {s["figure_id"]: s for s in dataset}
    records, meta = [], {}
    for i, fid in enumerate(sorted(cal_set)):
        s = by_id[fid]
        rec = orch.run_for_figure(
            figure_id=fid, image_path=s["image_path"], context=s["context"],
            diagram_type=s["diagram_type"], prompt_name="P2",
        )
        rec.human_score = _human_score(i)
        records.append(rec)
        meta[fid] = {"image_path": s["image_path"], "context": s["context"],
                     "diagram_type": s["diagram_type"]}
        assert rec.rounds and rec.final_score.primary_mean() > 0

    # Split-leak guard: every looped figure is a calibration figure.
    assert_calibration_only([r.figure_id for r in records], list(cal_set))

    # Stage 4: preference pairs + one DPO round (artefact contract).
    pairs = build_pairs(records, meta, lambda_between=0.3)
    assert pairs, "expected at least one preference pair"
    artifact = _StubTrainer().fit(pairs=pairs, round_index=0, out_dir=tmp_path / "dpo")
    assert (artifact.lora_path / "adapter_config.json").exists()

    # Stage 5: held-out evaluation (critic vs injected human scores).
    critic = _StubCritic()
    critic_scores, human_scores = [], []
    for j, fid in enumerate(sorted(ho_set)):
        s = by_id[fid]
        critic_scores.append(
            critic.score(s["image_path"], s["reference"], s["context"], s["diagram_type"])
        )
        human_scores.append(_human_score(j))
    report = evaluate_held_out(critic_scores, human_scores)
    assert report.n_items == 4
    assert -1.0 <= report.krippendorff_alpha_primary <= 1.0
    assert report.mean_abs_delta_primary >= 0.0

    # Stage 6 core: WCAG SC 1.1.1 validation runs and returns a verdict.
    figs = [
        FigureRecord(figure_id="f1", eth_category=ETHCategory.SIMPLE,
                     alt="A clear description", long_description_id=None),
        FigureRecord(figure_id="f2", eth_category=ETHCategory.DECORATIVE,
                     alt="", long_description_id=None),
    ]
    assert isinstance(WCAGValidator().validate(figs), list)


def test_split_is_reproducible_and_partitions(tmp_path: Path) -> None:
    """The stratified split is deterministic and partitions every figure."""
    dataset = DatasetFactory("stem_alt")(manifest_path=str(FIXTURE))
    target = {
        ("chemistry", "simple"): 1, ("chemistry", "complex"): 1,
        ("physics", "simple"): 1, ("physics", "complex"): 1,
    }
    cal, ho = stratified_split(dataset.figures, target, seed=42)
    assert set(cal).isdisjoint(set(ho))
    assert len(set(cal) | set(ho)) == 8
    cal2, ho2 = stratified_split(dataset.figures, target, seed=42)
    assert cal == cal2 and ho == ho2


def test_split_leak_guard_rejects_held_out() -> None:
    """A held-out figure among the trace ids must raise (no train-on-test)."""
    import pytest

    with pytest.raises(ValueError, match="held-out leak"):
        assert_calibration_only(["cal_1", "held_out_x"], ["cal_1", "cal_2"])

    with pytest.raises(ValueError, match="empty"):
        assert_calibration_only(["cal_1"], [])
