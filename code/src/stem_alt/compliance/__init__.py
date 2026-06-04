"""Compliance module: DIAGRAM/WCAG linter + ETH four-category classifier."""

from __future__ import annotations

from .diagram_linter import DiagramLinter, DiagramRule, DiagramViolation
from .eth_categories import ETHCategory
from .wcag_validator import WCAGValidator, WCAGViolation

__all__ = [
    "DiagramLinter",
    "DiagramRule",
    "DiagramViolation",
    "ETHCategory",
    "WCAGValidator",
    "WCAGViolation",
]
