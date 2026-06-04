"""Publication-grade corpus stratification figure (pubfig, Nature spec).

Renders the domain x ETH-category census as a grouped bar chart sized to the
Nature single-column width, exported as PDF/SVG/PNG. The paper itself is
tables-only (the stratification ships as a booktabs table); this figure is for
the supplementary material and the repository.

Every count is derived from `data/corpus/manifest.csv`.

Usage:
    python analysis/make_publication_figure.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pubfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("make_publication_figure")

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / "data" / "corpus" / "manifest.csv"
OUT_DIR = HERE.parent / "manuscript" / "figures"

CATEGORY_ORDER = ["simple", "linked", "decorative", "complex"]
DOMAIN_ORDER = ["chemistry", "mathematics_cs", "biology", "physics"]
DOMAIN_LABELS = ["Chemistry", "Mathematics and CS", "Biology", "Physics"]


def main() -> None:
    df = pd.read_csv(MANIFEST, dtype=str).fillna("")
    cross = pd.crosstab(df["domain"], df["eth_category"])
    cross = cross.reindex(index=DOMAIN_ORDER, columns=CATEGORY_ORDER, fill_value=0)
    data = cross.to_numpy(dtype=float)  # shape (domain, category)

    fig = pubfig.bar(
        data,
        category_names=DOMAIN_LABELS,
        series_names=[c.capitalize() for c in CATEGORY_ORDER],
        x_label="STEM domain",
        y_label="Number of figures",
        title="Held-out corpus composition",
        theme=pubfig.get_theme("nature"),
        value_dtick=1,
    )
    paths = pubfig.batch_export(
        fig, OUT_DIR / "fig_corpus_stratification_pub",
        formats=("pdf", "svg", "png"), spec="nature", width="single", dpi=300,
    )
    LOGGER.info("Wrote: %s", ", ".join(p.name for p in paths))


if __name__ == "__main__":
    main()
