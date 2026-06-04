# Data

| Path | Contents |
|---|---|
| `corpus/` | Figures, manifest, splits. |
| `ratings/` | Frozen rubric, rating schema, and a labelled synthetic demo fixture. |
| `outputs/` | Pipeline outputs (loop traces, DPO checkpoints, evaluation reports). Empty until a run finishes. |

The 30-figure held-out corpus is the public release surface. A run produces the
calibration figures and pipeline outputs under `outputs/`. The corpus, manifest,
splits, and rubric release under CC-BY 4.0. See
[`docs/DATA_RELEASE.md`](../docs/DATA_RELEASE.md) for the Data Availability statement
and FAIR metadata.
