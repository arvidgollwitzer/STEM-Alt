"""CLI to acquire the corpus figures listed in ``data/corpus/manifest.csv``.

Thin wrapper over :func:`stem_alt.corpus.fetch.fetch_corpus_images`, which
holds the acquisition logic shared with ``pipeline/01_build_corpus.py``. Every
third-party figure is pulled from Wikimedia Commons (SVG rendered to PNG,
raster converted to the manifest's target format, GIF preserved) and written
to ``data/corpus/images/``. ``local://`` figures are produced separately by
``render_local_figures.py``.

Usage:
    python code/scripts/fetch_corpus_images.py                 # fetch all
    python code/scripts/fetch_corpus_images.py --width 1600
    python code/scripts/fetch_corpus_images.py --only chem_simple_h2o_lewis
    python code/scripts/fetch_corpus_images.py --skip-existing

Requires network access to commons.wikimedia.org and Pillow (in the stack).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stem_alt.corpus.fetch import FetchConfig, fetch_corpus_images

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
MANIFEST = PROJECT_ROOT / "data" / "corpus" / "manifest.csv"


def main() -> int:
    """Parse CLI flags and fetch the manifest figures; return a shell exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1400, help="max render width (px)")
    parser.add_argument("--skip-existing", action="store_true", help="do not overwrite")
    parser.add_argument("--only", type=str, default=None, help="fetch one figure_id")
    parser.add_argument("--delay", type=float, default=0.7, help="pause between downloads (s)")
    args = parser.parse_args()

    cfg = FetchConfig(
        width=args.width,
        skip_existing=args.skip_existing,
        only=args.only,
        delay=args.delay,
    )
    result = fetch_corpus_images(MANIFEST, PROJECT_ROOT, cfg)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
