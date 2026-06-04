"""Corpus stratification tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from stem_alt.compliance import ETHCategory
from stem_alt.corpus.dataset import StemAltDataset, StemFigure
from stem_alt.corpus.stratification import stratified_split


def _figure(figure_id: str, domain: str, category: ETHCategory) -> StemFigure:
    return StemFigure(
        figure_id=figure_id,
        source_url="https://example.org",
        licence="CC-BY-4.0",
        domain=domain,
        eth_category=category,
        diagram_type="Graph",
        expert_reference_description="A short reference.",
        short_alt="short alt",
        context_paragraph="surrounding context",
        image_path=f"data/corpus/images/{figure_id}.png",
        split="",
    )


def test_stratified_split_respects_cell_targets() -> None:
    figures = (
        [_figure(f"chem_simple_{i:02d}", "chemistry", ETHCategory.SIMPLE) for i in range(5)]
        + [_figure(f"chem_complex_{i:02d}", "chemistry", ETHCategory.COMPLEX) for i in range(8)]
        + [_figure(f"bio_complex_{i:02d}", "biology", ETHCategory.COMPLEX) for i in range(6)]
    )
    target = {
        ("chemistry", "simple"): 2,
        ("chemistry", "complex"): 3,
        ("biology", "complex"): 3,
    }
    calibration, held_out = stratified_split(figures, held_out_target_per_cell=target, seed=7)
    assert len(held_out) == 8
    assert len(calibration) == len(figures) - 8


def test_stratified_split_raises_when_cell_underfilled() -> None:
    figures = [_figure("only_one", "physics", ETHCategory.LINKED)]
    target = {("physics", "linked"): 2}
    with pytest.raises(ValueError):
        stratified_split(figures, held_out_target_per_cell=target, seed=0)


def test_dataset_loads_split_only(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "figure_id,source_url,licence,domain,eth_category,diagram_type,"
        "expert_reference_description,short_alt,context_paragraph,image_path,split\n"
        "a,https://x,CC-BY,physics,simple,Graph,ref,alt,ctx,img/a.png,calibration\n"
        "b,https://x,CC-BY,physics,complex,Graph,ref,alt,ctx,img/b.png,held_out\n",
        encoding="utf-8",
    )
    held = StemAltDataset(manifest_path=str(manifest), split="held_out")
    assert len(held) == 1
    assert held[0]["figure_id"] == "b"
