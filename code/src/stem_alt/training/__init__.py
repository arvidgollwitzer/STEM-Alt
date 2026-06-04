"""Training module: DPO Trainer Factory/Registry + preference-pair builder."""

from __future__ import annotations

import os
from typing import Callable, Dict, Type

from stem_alt.utils import import_modules

TRAINER_FACTORY: Dict[str, Type] = {}


def register_trainer(name: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        if name in TRAINER_FACTORY:
            raise ValueError(f"Trainer '{name}' already registered")
        TRAINER_FACTORY[name] = cls
        return cls

    return decorator


def TrainerFactory(name: str) -> Type:
    if name not in TRAINER_FACTORY:
        raise KeyError(
            f"No trainer registered under '{name}'. "
            f"Available: {sorted(TRAINER_FACTORY)}"
        )
    return TRAINER_FACTORY[name]


import_modules(os.path.dirname(__file__), "stem_alt.training")

__all__ = ["TRAINER_FACTORY", "register_trainer", "TrainerFactory"]
