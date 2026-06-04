"""Render the two locally-authored corpus figures.

The figures are `mathcs_complex_loss_landscape` (a two-parameter loss
surface) and `mathcs_complex_dynamic_programming` (an LCS dynamic
programming table). Both are released under CC-BY-4.0 by the author and
stamped into `data/corpus/images/`. Their visual structure matches the
descriptions and the ETH "complex" category that the corpus manifest
assigns to them.

Usage:
    python code/scripts/render_local_figures.py

The script uses only `numpy` and `matplotlib`, both in the runtime stack,
and renders deterministically so reviewers can reproduce the figures.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers the projection)

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
IMAGES_DIR = PROJECT_ROOT / "data" / "corpus" / "images"


def _render_loss_landscape(out_path: Path) -> None:
    """Two-parameter loss surface for a tiny MLP — analytic stand-in.

    The surface is a quadratic plus two Gaussian saddle/well bumps, designed
    to look like the canonical neural-net loss-landscape illustration: one
    deeper minimum, one local minimum, and a saddle region between them.
    The mathematics is intentionally simple so the figure is reproducible.
    """
    grid = np.linspace(-2.5, 2.5, 200)
    w1, w2 = np.meshgrid(grid, grid)
    base = 0.35 * (w1**2 + w2**2)
    deep_min = -2.4 * np.exp(-((w1 - 0.7) ** 2 + (w2 - 0.4) ** 2) / 0.6)
    local_min = -1.1 * np.exp(-((w1 + 1.2) ** 2 + (w2 + 1.0) ** 2) / 0.8)
    saddle = 0.6 * np.exp(-((w1 - 0.1) ** 2 + (w2 + 0.3) ** 2) / 1.4)
    loss = base + deep_min + local_min + saddle

    fig = plt.figure(figsize=(7.0, 5.2))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(
        w1,
        w2,
        loss,
        cmap=cm.viridis,
        linewidth=0,
        antialiased=True,
        rstride=4,
        cstride=4,
    )
    ax.contour(w1, w2, loss, zdir="z", offset=loss.min() - 0.5, cmap=cm.viridis, levels=14)
    ax.set_xlabel(r"weight $w_1$")
    ax.set_ylabel(r"weight $w_2$")
    ax.set_zlabel("loss")
    ax.set_title("Two-parameter loss landscape (illustrative)")
    ax.view_init(elev=28, azim=-60)
    fig.colorbar(surf, ax=ax, shrink=0.55, aspect=14, label="loss")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _render_lcs_dp_table(out_path: Path) -> None:
    """Longest-common-subsequence dynamic programming table.

    Strings are X = "AGCAT", Y = "GAC". The table follows the standard
    textbook recurrence; we mark filled cells with their LCS length and
    overlay arrows along one optimal traceback path so the figure reads
    as a working DP table rather than a heatmap.
    """
    x = "AGCAT"
    y = "GAC"
    m, n = len(x), len(y)
    dp = np.zeros((m + 1, n + 1), dtype=int)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i, j] = dp[i - 1, j - 1] + 1
            else:
                dp[i, j] = max(dp[i - 1, j], dp[i, j - 1])

    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    ax.imshow(dp, cmap=cm.Blues, vmin=0, vmax=dp.max() + 1)
    ax.set_xticks(range(n + 1))
    ax.set_yticks(range(m + 1))
    ax.set_xticklabels([""] + list(y))
    ax.set_yticklabels([""] + list(x))
    ax.set_xlabel("Y = " + " ".join(y))
    ax.set_ylabel("X = " + " ".join(x))
    ax.set_title("LCS dynamic programming table — X='AGCAT', Y='GAC'")

    for i in range(m + 1):
        for j in range(n + 1):
            ax.text(
                j,
                i,
                str(int(dp[i, j])),
                ha="center",
                va="center",
                fontsize=12,
                color="black" if dp[i, j] < dp.max() - 1 else "white",
            )

    # Optimal traceback: AC (length 2).
    i, j = m, n
    path = [(i, j)]
    while i > 0 and j > 0:
        if x[i - 1] == y[j - 1]:
            i, j = i - 1, j - 1
        elif dp[i - 1, j] >= dp[i, j - 1]:
            i -= 1
        else:
            j -= 1
        path.append((i, j))
    for (i1, j1), (i0, j0) in zip(path[:-1], path[1:], strict=True):
        ax.annotate(
            "",
            xy=(j1, i1),
            xytext=(j0, i0),
            arrowprops=dict(arrowstyle="->", lw=1.8, color="crimson"),
        )

    ax.set_xticks(np.arange(-0.5, n + 1, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, m + 1, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linewidth=0.6)
    ax.tick_params(which="minor", length=0)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    landscape = IMAGES_DIR / "mathcs_complex_loss_landscape.png"
    lcs = IMAGES_DIR / "mathcs_complex_dynamic_programming.png"
    _render_loss_landscape(landscape)
    _render_lcs_dp_table(lcs)
    print(f"Wrote {landscape}")
    print(f"Wrote {lcs}")


if __name__ == "__main__":
    main()
