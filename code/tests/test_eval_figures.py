"""Contract test for the evaluation-figure renderers.

Loads analysis/generate_eval_figures.py by path (it lives outside the package),
feeds it a tiny in-test report matching the documented input schema, and asserts
all four figures render. This locks the producer/consumer contract between
pipeline/05_evaluate.py (which emits the report) and the renderers, without
needing real convergence data. The report here is test data, not a result.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ANALYSIS = (
    Path(__file__).resolve().parents[2] / "analysis" / "generate_eval_figures.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("eval_figures", _ANALYSIS)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_report() -> dict:
    return {
        "rounds": [
            {"r": 0, "alpha_primary": 0.40,
             "alpha_per_dim": {"D1": 0.4, "D2": 0.4, "D3": 0.4, "D4": 0.5, "D5": 0.5},
             "mean_abs_delta": 1.1},
            {"r": 1, "alpha_primary": 0.72,
             "alpha_per_dim": {"D1": 0.7, "D2": 0.7, "D3": 0.7, "D4": 0.8, "D5": 0.8},
             "mean_abs_delta": 0.6},
        ],
        "held_out": [
            {"figure_id": "chemistry_simple_0", "domain": "chemistry",
             "eth_category": "simple", "c_primary": 4.0, "h_primary": 4.3},
            {"figure_id": "physics_complex_0", "domain": "physics",
             "eth_category": "complex", "c_primary": 3.2, "h_primary": 3.6},
        ],
    }


def test_render_all_writes_four_figures(tmp_path: Path) -> None:
    module = _load_module()
    module.render_all(_tiny_report(), tmp_path)
    for name in (
        "fig_convergence_curve.png",
        "fig_ch_scatter.png",
        "fig_per_dimension.png",
        "fig_residual_heatmap.png",
    ):
        out = tmp_path / name
        assert out.exists() and out.stat().st_size > 0, f"{name} not rendered"
    assert (tmp_path / "eval_report_used.json").exists()
