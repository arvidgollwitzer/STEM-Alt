"""Generator module: G Factory/Registry across closed-API providers."""

from __future__ import annotations

import os
from typing import Callable, Dict, Type

from stem_alt.utils import import_modules

from .base import AltTextGenerator

GENERATOR_FACTORY: Dict[str, Type[AltTextGenerator]] = {}


def register_generator(name: str) -> Callable[[Type[AltTextGenerator]], Type[AltTextGenerator]]:
    """Register an `AltTextGenerator` subclass under `name`."""

    def decorator(cls: Type[AltTextGenerator]) -> Type[AltTextGenerator]:
        if name in GENERATOR_FACTORY:
            raise ValueError(f"Generator '{name}' already registered")
        GENERATOR_FACTORY[name] = cls
        return cls

    return decorator


def GeneratorFactory(name: str) -> Type[AltTextGenerator]:
    if name not in GENERATOR_FACTORY:
        raise KeyError(
            f"No generator registered under '{name}'. "
            f"Available: {sorted(GENERATOR_FACTORY)}"
        )
    return GENERATOR_FACTORY[name]


import_modules(os.path.dirname(__file__), "stem_alt.generator")

__all__ = [
    "AltTextGenerator",
    "GENERATOR_FACTORY",
    "register_generator",
    "GeneratorFactory",
]
