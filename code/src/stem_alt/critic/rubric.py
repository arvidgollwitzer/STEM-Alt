"""Five-dimension scoring rubric. D1-D3 form the primary outcome."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict


class RubricDimension(str, Enum):
    D1_FACTUAL_CORRECTNESS = "D1_factual_correctness"
    D2_INFORMATION_SUFFICIENCY = "D2_information_sufficiency"
    D3_DOMAIN_ACCURACY = "D3_domain_accuracy"
    D4_HALLUCINATION = "D4_hallucination"
    D5_CONCISENESS = "D5_conciseness"


PRIMARY_DIMENSIONS = (
    RubricDimension.D1_FACTUAL_CORRECTNESS,
    RubricDimension.D2_INFORMATION_SUFFICIENCY,
    RubricDimension.D3_DOMAIN_ACCURACY,
)


SCALE_MIN = 1
SCALE_MAX = 5


@dataclass(frozen=True)
class RubricScore:
    """One full rating: five Likert scores plus a free-text critique."""

    D1_factual_correctness: int
    D2_information_sufficiency: int
    D3_domain_accuracy: int
    D4_hallucination: int
    D5_conciseness: int
    critique: str = ""

    def __post_init__(self) -> None:
        for dim in RubricDimension:
            value = getattr(self, dim.value)
            if not SCALE_MIN <= value <= SCALE_MAX:
                raise ValueError(
                    f"{dim.value}={value} outside [{SCALE_MIN}, {SCALE_MAX}]"
                )

    def primary_mean(self) -> float:
        """Mean of D1, D2, D3 (the pre-registered primary outcome)."""
        return (
            self.D1_factual_correctness
            + self.D2_information_sufficiency
            + self.D3_domain_accuracy
        ) / 3.0

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)
