"""Module-level logger with consistent formatting across the pipeline."""

from __future__ import annotations

import logging
import sys

_DEFAULT_FMT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger for `name`.

    Idempotent: re-entering with the same name reuses the existing handler.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_DEFAULT_FMT))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
