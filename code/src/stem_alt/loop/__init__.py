"""Loop module: G-C iteration orchestrator + convergence detection."""

from __future__ import annotations

from .convergence import ConvergenceCheck
from .orchestrator import LoopOrchestrator, LoopRecord, LoopRound

__all__ = ["LoopOrchestrator", "LoopRecord", "LoopRound", "ConvergenceCheck"]
