"""Shared utilities: logging, seeding, dynamic submodule import."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from .logging import get_logger
from .seed import set_seed

__all__ = ["get_logger", "set_seed", "import_modules"]


def import_modules(directory: str, package_path: str) -> Iterable[str]:
    """Auto-import every module in `directory` under `package_path`.

    This enables the Factory/Registry pattern: importing a subpackage
    triggers each module's `@register_*` decorator so the factory map is
    populated at import time.
    """
    imported: list[str] = []
    for _, name, ispkg in pkgutil.iter_modules([directory]):
        if ispkg or name.startswith("_"):
            continue
        full_name = f"{package_path}.{name}"
        importlib.import_module(full_name)
        imported.append(full_name)
    return imported
