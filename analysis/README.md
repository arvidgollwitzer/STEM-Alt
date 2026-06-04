# Analysis

Reproducible analysis scripts for STEM-Alt. The scripts live here. The figures,
table data, and CSVs they produce go to `../manuscript/`, which holds the
manuscript's supporting material.

## 1. Corpus characterisation

`analyze_corpus.py` reads the corpus manifest (`../data/corpus/manifest.csv`)
and produces the descriptive analysis of the 30-figure held-out evaluation set.

```bash
cd "Academic Ops/ETH/digital accessibility/project work"
python analysis/analyze_corpus.py
```

Outputs (`manuscript/figures/`):

| File | Content | Backing data |
|---|---|---|
| `fig1_stratification.png` | figures per STEM domain x ETH category | `data/fig1_stratification.csv` |
| `fig2_diagram_types.png` | DIAGRAM figure-type distribution | `data/fig2_diagram_types.csv` |
| `fig3_licences.png` | source-licence distribution | `data/fig3_licences.csv` |
| `fig4_short_alt_length.png` | short-alt length vs the 125-char DIAGRAM bound | `data/fig4_short_alt_length.csv` |
| `corpus_summary.json` | machine-readable summary + integrity checks | — |

Each panel writes the exact CSV it was rendered from, so every figure is
reproducible from data. `corpus_summary.json` cross-checks the corpus against
the manuscript. `matches_manuscript_table1` is `true` when the manifest holds
30 figures across 4 domains x 4 categories. `short_alt_violations` lists every
non-decorative figure whose short alt exceeds 125 characters; it is currently
empty, so the corpus meets its own DIAGRAM A.3 compliance claim.

## 2. Evaluation figures

`generate_eval_figures.py` renders the four evaluation figures referenced by
the manuscript's Evaluation section: the convergence curve, the critic-human
scatter, per-dimension agreement, and the residual-disagreement heatmap. It
consumes the held-out report written by `pipeline/05_evaluate.py`:

```bash
python analysis/generate_eval_figures.py --report outputs/<run>/held_out_report.json
# -> manuscript/figures/eval/
```

The module docstring documents the input schema, and
`code/tests/test_eval_figures.py` covers the renderers.

## 3. Publication-grade tables and figure (pubtab / pubfig)

`make_publication_tables.py` builds Excel inputs from the manifest. `pubtab`
converts them to booktabs LaTeX (`three_line` theme), ready to drop into the
Springer Nature manuscript:

```bash
python analysis/make_publication_tables.py
pubtab xlsx2tex manuscript/tables/corpus_stratification.xlsx \
  -o manuscript/tables/corpus_stratification.tex --theme three_line \
  --caption "Held-out evaluation corpus..." --label tab:corpus --col-spec lccccc
pubtab xlsx2tex manuscript/tables/corpus_composition.xlsx \
  -o manuscript/tables/corpus_composition.tex --theme three_line \
  --caption "Corpus composition..." --label tab:composition --col-spec llc
```

| Artefact | Role |
|---|---|
| `manuscript/tables/corpus_stratification.tex` | manuscript Table 1 (domain x category census), regenerable from data |
| `manuscript/tables/corpus_composition.tex` | supplementary table (DIAGRAM type + licence counts) |

`make_publication_figure.py` renders the stratification as a Nature-spec
grouped bar via `pubfig`, exported as PDF/SVG/PNG for the supplementary
material (the paper itself is tables-only):

```bash
python analysis/make_publication_figure.py
# -> manuscript/figures/fig_corpus_stratification_pub.{pdf,svg,png}
```

The **table** carries the exact-count census. The figure is a secondary,
fast-perception view for the supplement.

## Environment

The descriptive scripts use `pandas`, `matplotlib`, and `numpy` (already in the
runtime stack). The publication artefacts additionally use `pubtab`, `pubfig`,
and `openpyxl`, declared under the `analysis` optional-dependency group:

```bash
cd code && uv pip install -e ".[analysis]"
```

Figures use the colour-blind safe Okabe-Ito palette (descriptive) and the
`pubfig` Nature theme (publication), in keeping with the project's
accessibility focus.
