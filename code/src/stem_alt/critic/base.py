"""Abstract base for the critic C."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from stem_alt.critic.rubric import RubricScore


class CriticBase(ABC):
    """Base class for C."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.name = getattr(cfg, "name", self.__class__.__name__)

    @abstractmethod
    def score(
        self,
        image_path: str,
        candidate_text: str,
        context: str,
        diagram_type: str,
    ) -> RubricScore:
        """Score one (figure, candidate alt-text) pair on the rubric."""
        raise NotImplementedError
