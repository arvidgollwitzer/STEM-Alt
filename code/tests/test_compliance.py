"""DIAGRAM linter + WCAG validator + ETH category."""

from __future__ import annotations

import pytest

from stem_alt.compliance import (
    DiagramLinter,
    DiagramRule,
    ETHCategory,
    WCAGValidator,
)
from stem_alt.compliance.wcag_validator import FigureRecord


def test_decorative_requires_empty_alt_and_no_long_desc() -> None:
    linter = DiagramLinter()
    violations = linter.lint(ETHCategory.DECORATIVE, "non-empty", "")
    assert any(v.rule is DiagramRule.DECORATIVE_EMPTY for v in violations)


def test_complex_requires_long_description_minimum_length() -> None:
    linter = DiagramLinter()
    violations = linter.lint(ETHCategory.COMPLEX, "short alt", "too short")
    assert any(v.rule is DiagramRule.COMPLEX_HAS_LONG_DESC for v in violations)


def test_simple_short_alt_length_cap() -> None:
    linter = DiagramLinter()
    long_alt = "x" * 130
    violations = linter.lint(ETHCategory.SIMPLE, long_alt, "")
    assert any(v.rule is DiagramRule.CONCISE for v in violations)


def test_pedagogical_phrasing_flagged() -> None:
    linter = DiagramLinter()
    long_desc = (
        "A bar chart compares two cohorts. "
        + "The goal of this figure is to teach you that they differ markedly across years."
    )
    violations = linter.lint(ETHCategory.COMPLEX, "alt", long_desc)
    assert any(v.rule is DiagramRule.OBJECTIVE for v in violations)


def test_wcag_validator_rejects_missing_alt() -> None:
    validator = WCAGValidator()
    figures = [
        FigureRecord(
            figure_id="a",
            eth_category=ETHCategory.SIMPLE,
            alt=None,
            long_description_id=None,
        )
    ]
    violations = validator.validate(figures)
    assert violations and violations[0].figure_id == "a"


def test_wcag_validator_accepts_decorative_with_empty_alt() -> None:
    validator = WCAGValidator()
    figures = [
        FigureRecord(
            figure_id="d",
            eth_category=ETHCategory.DECORATIVE,
            alt="",
            long_description_id=None,
        )
    ]
    assert validator.validate(figures) == []


def test_eth_category_from_label_normalises() -> None:
    assert ETHCategory.from_label("Complex") is ETHCategory.COMPLEX
    with pytest.raises(ValueError):
        ETHCategory.from_label("not-a-category")
