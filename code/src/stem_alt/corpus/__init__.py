"""Corpus module: dataset Factory/Registry + stratified split helpers."""

from __future__ import annotations

import os
from typing import Callable, Dict, Type

from torch.utils.data import Dataset

from stem_alt.utils import import_modules

DATASET_FACTORY: Dict[str, Type[Dataset]] = {}


def register_dataset(name: str) -> Callable[[Type[Dataset]], Type[Dataset]]:
    """Register a Dataset class under `name`.

    Usage:
        @register_dataset("stem_alt")
        class StemAltDataset(Dataset):
            ...
    """

    def decorator(cls: Type[Dataset]) -> Type[Dataset]:
        if name in DATASET_FACTORY:
            raise ValueError(f"Dataset '{name}' already registered")
        DATASET_FACTORY[name] = cls
        return cls

    return decorator


def DatasetFactory(name: str) -> Type[Dataset]:
    """Return the Dataset class registered under `name`.

    Falls back to the `stem_alt` default if the requested name is missing.
    """
    if name not in DATASET_FACTORY:
        if "stem_alt" in DATASET_FACTORY:
            return DATASET_FACTORY["stem_alt"]
        raise KeyError(f"No dataset registered under '{name}'")
    return DATASET_FACTORY[name]


# Auto-import all sibling modules so their @register_dataset decorators fire.
import_modules(os.path.dirname(__file__), "stem_alt.corpus")

__all__ = ["DATASET_FACTORY", "register_dataset", "DatasetFactory"]
