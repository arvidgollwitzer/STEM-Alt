"""Stage 6: package the release distribution.

Bundles the LoRA checkpoint, the corpus manifest, the rubric, the human
rating ledger, the held-out evaluation report, and the born-accessible
release page into `outputs/release/`. Verifies WCAG SC 1.1.1 on the
release HTML before sealing the bundle.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from html.parser import HTMLParser
from pathlib import Path
from typing import List

import hydra
from omegaconf import DictConfig

from stem_alt.compliance import ETHCategory, WCAGValidator
from stem_alt.compliance.wcag_validator import FigureRecord
from stem_alt.utils import get_logger

LOGGER = get_logger(__name__)


class _FigureExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.figures: List[FigureRecord] = []

    def handle_starttag(self, tag: str, attrs):
        if tag != "img":
            return
        a = dict(attrs)
        try:
            cat = ETHCategory(a.get("data-eth-category", "simple"))
        except ValueError:
            cat = ETHCategory.SIMPLE
        self.figures.append(
            FigureRecord(
                figure_id=a.get("data-figure-id", a.get("src", "<unknown>")),
                eth_category=cat,
                alt=a.get("alt"),
                long_description_id=a.get("aria-describedby"),
            )
        )


def _hash(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()[:16]


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    release_root = Path(cfg.output_dir) / "release"
    release_root.mkdir(parents=True, exist_ok=True)

    # 1. LoRA checkpoint
    lora_src = Path(cfg.output_dir) / "dpo"
    if lora_src.exists():
        shutil.copytree(lora_src, release_root / "lora", dirs_exist_ok=True)

    # 2. Corpus + rubric + ratings
    shutil.copy(cfg.corpus.manifest_path, release_root / "manifest.csv")
    shutil.copy(cfg.corpus.splits_path, release_root / "splits.json")
    rubric_src = Path("data/ratings/rubric.yaml")
    if rubric_src.exists():
        shutil.copy(rubric_src, release_root / "rubric.yaml")
    for ratings_path in (Path(cfg.output_dir) / "ratings.jsonl",
                         Path(cfg.output_dir) / "ratings_heldout.jsonl"):
        if ratings_path.exists():
            shutil.copy(ratings_path, release_root / ratings_path.name)

    # 3. Held-out report
    report = Path(cfg.output_dir) / "held_out_report.json"
    if report.exists():
        shutil.copy(report, release_root / "held_out_report.json")

    # 4. Born-accessible HTML release: copy from `release/` and lint.
    for asset in Path("release").glob("*"):
        shutil.copy(asset, release_root / asset.name)
    extractor = _FigureExtractor()
    for html_path in release_root.glob("*.html"):
        extractor.feed(html_path.read_text(encoding="utf-8"))
    violations = WCAGValidator().validate(extractor.figures)
    if violations:
        raise RuntimeError(
            "WCAG SC 1.1.1 violations in release HTML: "
            + json.dumps([v.__dict__ for v in violations], indent=2)
        )

    # 5. Provenance manifest
    files = sorted(p for p in release_root.rglob("*") if p.is_file())
    manifest = {
        "files": [
            {"path": str(p.relative_to(release_root)), "sha256_prefix": _hash(p)}
            for p in files
        ]
    }
    (release_root / "PROVENANCE.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    LOGGER.info("Release bundle sealed at %s (%d files).", release_root, len(files))


if __name__ == "__main__":
    main()
