"""Critic module: C Factory/Registry. LLaVA-Next-7B + LoRA is the default."""

from __future__ import annotations

import os
from typing import Callable, Dict, Type

from stem_alt.utils import import_modules

from .base import CriticBase
from .rubric import RubricDimension, RubricScore

CRITIC_FACTORY: Dict[str, Type[CriticBase]] = {}


def register_critic(name: str) -> Callable[[Type[CriticBase]], Type[CriticBase]]:
    def decorator(cls: Type[CriticBase]) -> Type[CriticBase]:
        if name in CRITIC_FACTORY:
            raise ValueError(f"Critic '{name}' already registered")
        CRITIC_FACTORY[name] = cls
        return cls

    return decorator


def CriticFactory(name: str) -> Type[CriticBase]:
    if name not in CRITIC_FACTORY:
        raise KeyError(
            f"No critic registered under '{name}'. "
            f"Available: {sorted(CRITIC_FACTORY)}"
        )
    return CRITIC_FACTORY[name]


import_modules(os.path.dirname(__file__), "stem_alt.critic")

__all__ = [
    "CriticBase",
    "RubricDimension",
    "RubricScore",
    "CRITIC_FACTORY",
    "register_critic",
    "CriticFactory",
]
