"""StemAltDataset: figures + metadata + DIAGRAM type + ETH category."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from torch.utils.data import Dataset

from stem_alt.compliance import ETHCategory
from stem_alt.corpus import register_dataset


@dataclass(frozen=True)
class StemFigure:
    """One row of the corpus manifest."""

    figure_id: str
    source_url: str
    licence: str
    domain: str
    eth_category: ETHCategory
    diagram_type: str
    expert_reference_description: str
    short_alt: str
    context_paragraph: str
    image_path: str
    split: str

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> "StemFigure":
        return cls(
            figure_id=row["figure_id"],
            source_url=row["source_url"],
            licence=row["licence"],
            domain=row["domain"],
            eth_category=ETHCategory(row["eth_category"]),
            diagram_type=row["diagram_type"],
            expert_reference_description=row["expert_reference_description"],
            short_alt=row["short_alt"],
            context_paragraph=row["context_paragraph"],
            image_path=row["image_path"],
            split=row["split"],
        )


@register_dataset("stem_alt")
class StemAltDataset(Dataset):
    """The full STEM-Alt corpus.

    Wraps a `manifest.csv` and exposes `StemFigure` rows. Stratification
    helpers in `stratification.py` produce calibration/held-out splits
    without ever moving figures between them after the freeze.
    """

    def __init__(self, manifest_path: str, split: Optional[str] = None) -> None:
        super().__init__()
        self.manifest_path = Path(manifest_path)
        self.split = split
        self._rows = self._load(self.manifest_path, split)

    @staticmethod
    def _load(path: Path, split: Optional[str]) -> List[StemFigure]:
        rows: List[StemFigure] = []
        with path.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if split is None or row["split"] == split:
                    rows.append(StemFigure.from_row(row))
        return rows

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        fig = self._rows[idx]
        return {
            "figure_id": fig.figure_id,
            "image_path": fig.image_path,
            "context": fig.context_paragraph,
            "domain": fig.domain,
            "eth_category": fig.eth_category.value,
            "diagram_type": fig.diagram_type,
            "reference": fig.expert_reference_description,
            "short_alt": fig.short_alt,
            "split": fig.split,
        }

    @property
    def figures(self) -> List[StemFigure]:
        """Direct access to the underlying `StemFigure` rows."""
        return list(self._rows)
