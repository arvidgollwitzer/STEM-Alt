# Corpus

The corpus is designed as 150 openly licensed STEM figures in two splits:

- **calibration** (120 figures): drive the loop and DPO fine-tuning. Reconstructed
  by `pipeline/01_build_corpus.py` as figures are ingested; not shipped in the repo.
- **held_out** (30 figures): never enter fine-tuning, and the surface against which
  the pre-registered convergence threshold is evaluated. This split is what ships in
  `manifest.csv`.

The figures come from OpenStax, MIT OpenCourseWare, arXiv CC-BY, and Wikimedia Commons.

## Files

| File | Purpose |
|---|---|
| `manifest.csv` | One row per figure with provenance, licence, domain, ETH category, DIAGRAM type, expert reference description, short alt, context paragraph, image path, and split. |
| `splits.json` | Frozen calibration / held-out assignment. Cannot change after the freeze. |

## Stratification

The corpus stratifies on two axes: 4 domains × 4 ETH categories = 16 cells.
`manuscript/tables/table1_corpus.md` lists the per-cell counts for the 30-figure
held-out subset.

## Licences

Each figure retains its original licence: CC-BY, CC-BY-SA, or the source's
public-domain equivalent. The aggregated manifest, splits, and rubric release
under CC-BY 4.0. See [`../../docs/DATA_RELEASE.md`](../../docs/DATA_RELEASE.md) for the
Data Availability statement and FAIR metadata.

## Adding figures

1. Append a row to `manifest.csv` with all columns populated.
2. Place the image file under `data/corpus/images/`.
3. Run `pipeline/01_build_corpus.py` to validate and to re-emit `splits.json`.

At build time, the pipeline rejects any row that fails the DIAGRAM linter.
