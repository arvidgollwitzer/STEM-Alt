"""Abstract base for closed-API alt-text generators.

Models are config-driven: `__init__` accepts only a `cfg` namespace.
Subclasses register themselves via `@register_generator(name)`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class GenerationResult:
    """One alt-text candidate plus provenance for logging."""

    figure_id: str
    text: str
    prompt_name: str
    model_version: str
    decoding_params: str
    timestamp: str
    round_index: int = 0
    critic_critique: Optional[str] = None


class AltTextGenerator(ABC):
    """Base class for G."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.name = getattr(cfg, "name", self.__class__.__name__)
        self.model_version = getattr(cfg, "model_version", "unknown")
        self.temperature = getattr(cfg, "temperature", 0.0)

    @abstractmethod
    def generate(
        self,
        image_path: str,
        context: str,
        prompt_name: str,
        previous_critique: Optional[str] = None,
        round_index: int = 0,
    ) -> GenerationResult:
        """Produce one alt-text candidate.

        `previous_critique` is None on round 0 and carries C's feedback on
        subsequent rounds. `round_index` starts at 0 for the unrevised draft.
        """
        raise NotImplementedError
