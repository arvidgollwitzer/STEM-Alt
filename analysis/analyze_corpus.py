"""Corpus characterisation analysis for the STEM-Alt held-out evaluation set.

This script reads the released corpus manifest (`data/corpus/manifest.csv`)
and produces the descriptive analysis of the figures that have actually been
collected: the stratification matrix, the DIAGRAM figure-type distribution,
the source-licence distribution, and the short-alt length profile against the
DIAGRAM 125-character bound. Every figure is written alongside the exact CSV
that produced it, so each panel is reproducible from data.

This is a characterisation of the corpus artefact. It does not report any
generator, critic, or human-rating outcome; those require running the loop
and collecting ratings (see `analysis/generate_eval_figures.py` for the
figure generators that consume that data once it exists).

Usage:
    python analysis/analyze_corpus.py

Outputs (under analysis/figures/):
    fig1_stratification.png          domain x ETH category counts
    fig2_diagram_types.png           DIAGRAM figure-type distribution
    fig3_licences.png                source-licence distribution
    fig4_short_alt_length.png        short-alt char length vs 125-char bound
    data/*.csv                       the table behind each figure
    corpus_summary.json              machine-readable summary + integrity checks
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("analyze_corpus")

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
MANIFEST = PROJECT_ROOT / "data" / "corpus" / "manifest.csv"
# Figures and their backing CSVs are supporting material for the manuscript,
# so the analysis scripts write into manuscript/figures (manuscript/ holds the
# figures, table data, and metadata; analysis/ holds the scripts that make it).
FIG_DIR = PROJECT_ROOT / "manuscript" / "figures"
DATA_DIR = FIG_DIR / "data"

# ETH alt-text categories and STEM domains, in the canonical display order
# used by the manuscript (Table 1).
CATEGORY_ORDER: List[str] = ["simple", "linked", "decorative", "complex"]
DOMAIN_ORDER: List[str] = ["chemistry", "mathematics_cs", "biology", "physics"]
DOMAIN_LABELS: Dict[str, str] = {
    "chemistry": "Chemistry",
    "mathematics_cs": "Mathematics and CS",
    "biology": "Biology",
    "physics": "Physics",
}

# Colour-blind-safe qualitative palette (Okabe-Ito). The corpus is an
# accessibility artefact, so its own figures use an accessible palette.
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#F0E442", "#999999"]

# DIAGRAM Image Description Guidelines A.3: short alt is bounded at 125
# characters where the image type permits.
SHORT_ALT_BOUND = 125


def load_manifest() -> pd.DataFrame:
    """Load the corpus manifest, validating the expected schema."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST}")
    df = pd.read_csv(MANIFEST, dtype=str).fillna("")
    expected = {
        "figure_id", "source_url", "licence", "domain", "eth_category",
        "diagram_type", "expert_reference_description", "short_alt",
        "context_paragraph", "image_path", "split",
    }
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Manifest is missing columns: {sorted(missing)}")
    LOGGER.info("Loaded %d figures from %s", len(df), MANIFEST.name)
    return df


def _save_panel(fig: plt.Figure, name: str) -> None:
    fig.savefig(FIG_DIR / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    LOGGER.info("Wrote figures/%s.png", name)


def stratification(df: pd.DataFrame) -> pd.DataFrame:
    """Domain x ETH-category count matrix (manuscript Table 1)."""
    cross = pd.crosstab(df["domain"], df["eth_category"])
    cross = cross.reindex(index=DOMAIN_ORDER, columns=CATEGORY_ORDER, fill_value=0)
    cross.index = [DOMAIN_LABELS[d] for d in cross.index]
    cross["Total"] = cross.sum(axis=1)
    cross.loc["Total"] = cross.sum(axis=0)
    cross.to_csv(DATA_DIR / "fig1_stratification.csv")

    # Grouped bars: exact per-cell counts are legible and the complex-weighting
    # pattern is visible at a glance. Stacked bars hide both. The legend sits
    # below the axes so it never overlaps the data.
    plot = cross.drop(index="Total", columns="Total")
    domains = list(plot.index)
    x = np.arange(len(domains))
    n_cat = len(CATEGORY_ORDER)
    width = 0.20
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for i, cat in enumerate(CATEGORY_ORDER):
        offset = (i - (n_cat - 1) / 2) * width
        bars = ax.bar(x + offset, plot[cat].to_numpy(), width, label=cat,
                      color=OKABE_ITO[i % len(OKABE_ITO)], edgecolor="white", linewidth=0.5)
        ax.bar_label(bars, padding=2, fontsize=8, color="#333333")
    ax.set_xticks(x)
    ax.set_xticklabels(domains)
    ax.set_ylabel("Number of figures")
    ax.set_title("Corpus stratification by STEM domain and ETH alt-text category", pad=12)
    ax.set_ylim(0, float(plot.to_numpy().max()) + 0.8)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(title="ETH category", frameon=False, ncol=n_cat,
              loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    _save_panel(fig, "fig1_stratification")
    return cross


def diagram_types(df: pd.DataFrame) -> pd.DataFrame:
    """DIAGRAM figure-type distribution."""
    counts = df["diagram_type"].value_counts().sort_values(ascending=True)
    counts.to_csv(DATA_DIR / "fig2_diagram_types.csv", header=["count"])

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.barh(counts.index, counts.values, color=OKABE_ITO[0])
    for y, v in enumerate(counts.values):
        ax.text(v + 0.05, y, str(int(v)), va="center", fontsize=9)
    ax.set_xlabel("Number of figures")
    ax.set_title("DIAGRAM figure-type distribution")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save_panel(fig, "fig2_diagram_types")
    return counts.to_frame("count")


def licences(df: pd.DataFrame) -> pd.DataFrame:
    """Source-licence distribution, separating local CC-BY-4.0 renders."""
    counts = df["licence"].value_counts().sort_values(ascending=False)
    counts.to_csv(DATA_DIR / "fig3_licences.csv", header=["count"])

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar(counts.index, counts.values,
           color=[OKABE_ITO[i % len(OKABE_ITO)] for i in range(len(counts))])
    for x, v in enumerate(counts.values):
        ax.text(x, v + 0.1, str(int(v)), ha="center", fontsize=9)
    ax.set_ylabel("Number of figures")
    ax.set_title("Source-licence distribution")
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=30, ha="right", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save_panel(fig, "fig3_licences")
    return counts.to_frame("count")


def short_alt_length(df: pd.DataFrame) -> pd.DataFrame:
    """Short-alt character length against the DIAGRAM 125-character bound.

    Decorative figures carry an empty short alt by design (WCAG decorative
    image handling), so they are reported separately rather than as a
    length violation.
    """
    out = df[["figure_id", "eth_category", "short_alt"]].copy()
    out["short_alt_chars"] = out["short_alt"].str.len()
    out["is_decorative"] = out["eth_category"] == "decorative"
    out["within_bound"] = (out["short_alt_chars"] <= SHORT_ALT_BOUND) | out["is_decorative"]
    out.to_csv(DATA_DIR / "fig4_short_alt_length.csv", index=False)

    non_dec = out[~out["is_decorative"]]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.hist(non_dec["short_alt_chars"], bins=range(0, SHORT_ALT_BOUND + 30, 10),
            color=OKABE_ITO[2], edgecolor="white")
    ax.axvline(SHORT_ALT_BOUND, color=OKABE_ITO[3], linestyle="--",
               label=f"DIAGRAM A.3 bound ({SHORT_ALT_BOUND} chars)")
    ax.set_xlabel("Short-alt length (characters)")
    ax.set_ylabel("Number of non-decorative figures")
    ax.set_title("Short-alt length vs the DIAGRAM 125-character bound")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save_panel(fig, "fig4_short_alt_length")
    return out


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = load_manifest()

    cross = stratification(df)
    diagram_types(df)
    licences(df)
    alt = short_alt_length(df)

    # Integrity checks: the analysis must agree with the manuscript's frozen
    # numbers, and the corpus must respect its own compliance claims.
    n_total = int(len(df))
    n_decorative = int((df["eth_category"] == "decorative").sum())
    violations = alt[(~alt["within_bound"])]["figure_id"].tolist()
    summary = {
        "n_figures": n_total,
        "n_domains": int(df["domain"].nunique()),
        "n_eth_categories": int(df["eth_category"].nunique()),
        "n_diagram_types": int(df["diagram_type"].nunique()),
        "n_licences": int(df["licence"].nunique()),
        "n_decorative_empty_alt": n_decorative,
        "short_alt_bound": SHORT_ALT_BOUND,
        "short_alt_violations": violations,
        "matches_manuscript_table1": bool(
            n_total == 30
            and int(cross.loc["Total", "Total"]) == 30
            and df["domain"].nunique() == 4
            and df["eth_category"].nunique() == 4
        ),
    }
    (FIG_DIR / "corpus_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    LOGGER.info("Corpus summary: %s", json.dumps(summary))
    if violations:
        LOGGER.warning("Short-alt length violations: %s", violations)
    else:
        LOGGER.info("All non-decorative short alts respect the %d-char bound.", SHORT_ALT_BOUND)


if __name__ == "__main__":
    main()
