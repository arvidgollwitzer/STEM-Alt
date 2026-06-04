"""DIAGRAM general-rule linter.

Runs at corpus build time and on every loop output. A failure here is
treated as a generation error, not as a rating dimension. The linter is
intentionally strict: it errs on the side of refusing borderline outputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence

from stem_alt.compliance.eth_categories import ETHCategory

SHORT_ALT_CHAR_LIMIT = 125
LONG_DESCRIPTION_MIN_CHARS = 80


class DiagramRule(str, Enum):
    AUDIENCE = "audience"
    CONCISE = "concise"
    OBJECTIVE = "objective"
    GENERAL_TO_SPECIFIC = "general_to_specific"
    TONE = "tone"
    DECORATIVE_EMPTY = "decorative_empty"
    COMPLEX_HAS_LONG_DESC = "complex_has_long_desc"


@dataclass(frozen=True)
class DiagramViolation:
    rule: DiagramRule
    message: str


# Heuristic vocabulary for the objective/tone rules. Kept short on purpose
# so the linter is conservative rather than chatty.
_PEDAGOGY_PHRASES = (
    "this teaches",
    "the author wants",
    "the goal of this figure",
    "this demonstrates that",
    "as you can see",
)


class DiagramLinter:
    """Apply the DIAGRAM general rules to a candidate description."""

    def lint(
        self,
        eth_category: ETHCategory,
        short_alt: str,
        long_description: str,
    ) -> List[DiagramViolation]:
        violations: List[DiagramViolation] = []

        if eth_category is ETHCategory.DECORATIVE:
            if short_alt.strip() or long_description.strip():
                violations.append(
                    DiagramViolation(
                        DiagramRule.DECORATIVE_EMPTY,
                        "Decorative figures require alt='' and no long description.",
                    )
                )
            return violations

        if eth_category is ETHCategory.COMPLEX:
            if len(long_description.strip()) < LONG_DESCRIPTION_MIN_CHARS:
                violations.append(
                    DiagramViolation(
                        DiagramRule.COMPLEX_HAS_LONG_DESC,
                        f"Complex figures require a long description of at least "
                        f"{LONG_DESCRIPTION_MIN_CHARS} characters.",
                    )
                )

        if len(short_alt) > SHORT_ALT_CHAR_LIMIT and eth_category in (
            ETHCategory.SIMPLE,
            ETHCategory.LINKED,
        ):
            violations.append(
                DiagramViolation(
                    DiagramRule.CONCISE,
                    f"Short alt exceeds {SHORT_ALT_CHAR_LIMIT} characters.",
                )
            )

        text_for_objective = (short_alt + " " + long_description).lower()
        if any(phrase in text_for_objective for phrase in _PEDAGOGY_PHRASES):
            violations.append(
                DiagramViolation(
                    DiagramRule.OBJECTIVE,
                    "Pedagogical interpretation detected; describe what is visible.",
                )
            )

        if long_description:
            opener = long_description.strip().split(".", maxsplit=1)[0]
            if len(opener.split()) > 30:
                violations.append(
                    DiagramViolation(
                        DiagramRule.GENERAL_TO_SPECIFIC,
                        "Opening sentence exceeds 30 words; lead with a single-sentence summary.",
                    )
                )
            if _has_passive_voice(long_description):
                violations.append(
                    DiagramViolation(
                        DiagramRule.TONE,
                        "Passive constructions detected; prefer active verbs in present tense.",
                    )
                )

        return violations


_PASSIVE_RE = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+\w+ed\b", re.IGNORECASE
)


def _has_passive_voice(text: str) -> bool:
    return _PASSIVE_RE.search(text) is not None


def first_violation_message(violations: Sequence[DiagramViolation]) -> Optional[str]:
    return violations[0].message if violations else None
