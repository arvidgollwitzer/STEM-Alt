"""Evaluation-figure generators for the STEM-Alt convergence study.

These generators turn the study's output into the four evaluation figures
referenced by the manuscript's Evaluation section:

    fig_convergence_curve   Krippendorff alpha (C vs H) against DPO round r
    fig_ch_scatter          per-figure C-score vs H-score on the held-out split
    fig_per_dimension       per-dimension C-H alpha (D1..D5)
    fig_residual_heatmap    residual C-H disagreement by domain x category

INPUT SCHEMA
------------
The generators consume a single JSON object with two keys:

    {
      "rounds": [
        {"r": 0, "alpha_primary": <float>, "alpha_per_dim": {"D1":..,"D5":..},
         "mean_abs_delta": <float>}
        , ...
      ],
      "held_out": [
        {"figure_id": <str>, "domain": <str>, "eth_category": <str>,
         "c_primary": <float>, "h_primary": <float>}
        , ...
      ]
    }

`rounds` is the per-DPO-round convergence trace; `held_out` is the final-round
per-figure critic/human primary-outcome pair. The object is the held-out report
written by `pipeline/05_evaluate.py`; this script only renders it. The renderers
are covered by `code/tests/test_eval_figures.py`.

USAGE
-----
    python analysis/generate_eval_figures.py --report path/to/held_out_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("generate_eval_figures")

HERE = Path(__file__).resolve().parent
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7"]
DIMENSIONS = ["D1", "D2", "D3", "D4", "D5"]
DOMAINS = ["chemistry", "mathematics_cs", "biology", "physics"]
CATEGORIES = ["simple", "linked", "decorative", "complex"]
CONVERGENCE_THRESHOLD = 0.70


def fig_convergence_curve(report: Dict, out_dir: Path) -> None:
    rounds = report["rounds"]
    r = [x["r"] for x in rounds]
    a = [x["alpha_primary"] for x in rounds]
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(r, a, marker="o", color=OKABE_ITO[0], label="C-H Krippendorff alpha")
    ax.axhline(CONVERGENCE_THRESHOLD, color=OKABE_ITO[3], linestyle="--",
               label=f"threshold ({CONVERGENCE_THRESHOLD})")
    ax.set_xlabel("DPO round r")
    ax.set_ylabel("Krippendorff alpha (primary outcome)")
    ax.set_title("Critic-human convergence across DPO rounds")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_convergence_curve.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_ch_scatter(report: Dict, out_dir: Path) -> None:
    ho = report["held_out"]
    c = [x["c_primary"] for x in ho]
    h = [x["h_primary"] for x in ho]
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    ax.scatter(h, c, color=OKABE_ITO[0], alpha=0.75, edgecolor="white")
    ax.plot([1, 5], [1, 5], color="#999999", linestyle=":", label="perfect agreement")
    ax.set_xlabel("Human primary-outcome score")
    ax.set_ylabel("Critic primary-outcome score")
    ax.set_title("Critic vs human on the held-out split")
    ax.set_xlim(1, 5)
    ax.set_ylim(1, 5)
    ax.set_aspect("equal")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_ch_scatter.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_per_dimension(report: Dict, out_dir: Path) -> None:
    final = report["rounds"][-1]["alpha_per_dim"]
    vals = [final[d] for d in DIMENSIONS]
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.bar(DIMENSIONS, vals, color=OKABE_ITO[2])
    ax.axhline(CONVERGENCE_THRESHOLD, color=OKABE_ITO[3], linestyle="--")
    for x, v in enumerate(vals):
        ax.text(x, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylabel("Krippendorff alpha")
    ax.set_title("Per-dimension critic-human agreement (final round)")
    ax.set_ylim(0, 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_per_dimension.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_residual_heatmap(report: Dict, out_dir: Path) -> None:
    grid = np.full((len(DOMAINS), len(CATEGORIES)), np.nan)
    acc: Dict = {}
    for x in report["held_out"]:
        key = (x["domain"], x["eth_category"])
        acc.setdefault(key, []).append(abs(x["c_primary"] - x["h_primary"]))
    for i, d in enumerate(DOMAINS):
        for j, cat in enumerate(CATEGORIES):
            vals = acc.get((d, cat))
            if vals:
                grid[i, j] = float(np.mean(vals))
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    vmax = float(np.nanmax(grid)) if np.isfinite(grid).any() else 1.0
    im = ax.imshow(grid, cmap="YlOrRd", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(CATEGORIES)), CATEGORIES)
    ax.set_yticks(range(len(DOMAINS)), DOMAINS)
    for i in range(len(DOMAINS)):
        for j in range(len(CATEGORIES)):
            if np.isfinite(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:.2f}", ha="center", va="center", fontsize=9)
    ax.set_title("Mean residual |C - H| by domain and category")
    fig.colorbar(im, ax=ax, shrink=0.8, label="mean |C - H|")
    fig.tight_layout()
    fig.savefig(out_dir / "fig_residual_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def render_all(report: Dict, out_dir: Path) -> None:
    """Render all four evaluation figures from a held-out report into `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "eval_report_used.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    fig_convergence_curve(report, out_dir)
    fig_ch_scatter(report, out_dir)
    fig_per_dimension(report, out_dir)
    fig_residual_heatmap(report, out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, required=True,
        help="path to the held-out report JSON produced by pipeline/05_evaluate.py",
    )
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    out_dir = HERE.parent / "manuscript" / "figures" / "eval"
    render_all(report, out_dir)
    LOGGER.info("Wrote 4 evaluation figures to %s", out_dir.relative_to(HERE.parent))


if __name__ == "__main__":
    main()
