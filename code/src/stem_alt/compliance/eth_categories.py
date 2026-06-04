"""The ETH four-category alt-text taxonomy."""

from __future__ import annotations

from enum import Enum


class ETHCategory(str, Enum):
    SIMPLE = "simple"
    LINKED = "linked"
    DECORATIVE = "decorative"
    COMPLEX = "complex"

    @classmethod
    def from_label(cls, label: str) -> "ETHCategory":
        try:
            return cls(label.lower().strip())
        except ValueError as e:
            raise ValueError(
                f"Unknown ETH category '{label}'. "
                f"Allowed: {[c.value for c in cls]}"
            ) from e
