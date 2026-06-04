"""Render alt-text aloud via NVDA for screen-reader-user raters.

Two modes:
  - `live`: drive the NVDA process directly on a Windows rater workstation.
  - `offline`: synthesise a WAV file via the configured TTS so the rater
    can play back the same audio asynchronously. Used for remote raters
    and for fallback when NVDA is unavailable on the rating machine.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class NVDARenderer:
    mode: str = "offline"
    nvda_executable: Optional[str] = None
    offline_tts_command: str = "espeak-ng"

    def __post_init__(self) -> None:
        if self.mode not in {"live", "offline"}:
            raise ValueError(f"NVDARenderer.mode must be 'live' or 'offline', got {self.mode}")

    def render(self, text: str, out_path: Optional[Path] = None) -> Optional[Path]:
        """Render `text` for a rater. Returns the audio path in offline mode."""
        if self.mode == "live":
            if self.nvda_executable is None or not shutil.which(self.nvda_executable):
                raise RuntimeError("Live mode requires a working NVDA executable.")
            subprocess.run(
                [self.nvda_executable, "--say", text],
                check=True,
                capture_output=True,
            )
            return None
        if out_path is None:
            raise ValueError("Offline mode requires `out_path` for the WAV target.")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not shutil.which(self.offline_tts_command):
            raise RuntimeError(
                f"Offline mode requires the TTS command "
                f"'{self.offline_tts_command}' on PATH."
            )
        subprocess.run(
            [self.offline_tts_command, "-w", str(out_path), text],
            check=True,
            capture_output=True,
        )
        return out_path
