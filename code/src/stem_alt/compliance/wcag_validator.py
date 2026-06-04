"""WCAG 2.2 SC 1.1.1 validator.

Checks that every figure in a published artefact carries one of:
  - a non-empty `alt` attribute (informative content), OR
  - `alt=""` plus `role="presentation"` (decorative).

Designed for HTML and ePub3 outputs. Operates on a stream of figure tuples
parsed by the release pipeline; no HTML parsing logic lives here so the
linter is testable without a DOM.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence

from stem_alt.compliance.eth_categories import ETHCategory


class WCAGRule(str, Enum):
    NON_TEXT_REQUIRES_ALT = "1.1.1_non_text_requires_alt"
    DECORATIVE_REQUIRES_EMPTY_ALT = "1.1.1_decorative_requires_empty_alt"
    COMPLEX_REQUIRES_LONG_DESC = "1.1.1_complex_requires_long_desc_reference"


@dataclass(frozen=True)
class WCAGViolation:
    rule: WCAGRule
    figure_id: str
    message: str


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    eth_category: ETHCategory
    alt: Optional[str]
    long_description_id: Optional[str]


class WCAGValidator:
    """SC 1.1.1 enforcement across a published artefact."""

    def validate(self, figures: Sequence[FigureRecord]) -> List[WCAGViolation]:
        violations: List[WCAGViolation] = []
        for fig in figures:
            if fig.eth_category is ETHCategory.DECORATIVE:
                if fig.alt is None or fig.alt != "":
                    violations.append(
                        WCAGViolation(
                            WCAGRule.DECORATIVE_REQUIRES_EMPTY_ALT,
                            fig.figure_id,
                            "Decorative figures must declare alt=\"\".",
                        )
                    )
                continue
            if fig.alt is None or not fig.alt.strip():
                violations.append(
                    WCAGViolation(
                        WCAGRule.NON_TEXT_REQUIRES_ALT,
                        fig.figure_id,
                        "Informative figures must carry a non-empty alt.",
                    )
                )
                continue
            if fig.eth_category is ETHCategory.COMPLEX and not fig.long_description_id:
                violations.append(
                    WCAGViolation(
                        WCAGRule.COMPLEX_REQUIRES_LONG_DESC,
                        fig.figure_id,
                        "Complex figures must reference a long description via aria-describedby.",
                    )
                )
        return violations
