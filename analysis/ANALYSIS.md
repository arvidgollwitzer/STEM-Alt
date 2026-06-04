# STEM-Alt: Corpus Analysis Report

This report characterises the released STEM-Alt corpus. It is reproducible:
every number is emitted by `analyze_corpus.py` from the corpus manifest, and
every figure ships with the CSV it was rendered from (under
`manuscript/figures/`).

## Scope

The corpus characterisation below is computed from the 30-figure held-out
evaluation set in `data/corpus/manifest.csv`. The evaluation framework that
compares the calibrated critic against the human raters (Section 5) is
implemented and tested. Its four figures render from the held-out report that
`pipeline/05_evaluate.py` writes once the study runs on a machine with the
generator API keys and a GPU for the critic and DPO trainer. "Running the full
study" below documents the end-to-end run.

**Evaluation contract** (the manuscript's design): primary metric = Krippendorff's
alpha between the critic C and the human raters H on the mean of D1, D2, D3
(higher is better); unit of analysis = figure (held-out n = 30); convergence
threshold = alpha >= 0.70 sustained over two consecutive DPO rounds;
rating-quality floor = H1-H2 alpha >= 0.60; comparison family =
{B1, B2, B3, B4, STEM-Alt} plus generalisation conditions G1/G2/G3; error bars =
figure-stratified bootstrap (B = 2,000).

## 1. Corpus stratification

The held-out corpus holds 30 figures, balanced across four STEM domains and the
four ETH alt-text categories. This reproduces manuscript Table 1 exactly
(`corpus_summary.json`: `matches_manuscript_table1 = true`).

| Domain | Simple | Linked | Decorative | Complex | Total |
|---|---|---|---|---|---|
| Chemistry | 2 | 2 | 1 | 3 | 8 |
| Mathematics and CS | 2 | 2 | 1 | 3 | 8 |
| Biology | 1 | 2 | 1 | 3 | 7 |
| Physics | 1 | 2 | 1 | 3 | 7 |
| **Total** | **6** | **8** | **4** | **12** | **30** |

Complex figures dominate (12 of 30), which is deliberate: complex illustrations
are where AI alt-text fails hardest and where the critic is most needed.
Figure: `manuscript/figures/fig1_stratification.png`.

## 2. DIAGRAM figure-type coverage

The corpus spans nine DIAGRAM figure types. Graphs (8) and relational diagrams
(7) are the most frequent, matching the structure-heavy content of STEM
teaching material.

| DIAGRAM type | Count |
|---|---|
| Graphs | 8 |
| Relational Diagrams | 7 |
| Illustrated Diagrams | 4 |
| Photos | 4 |
| Chemistry | 2 |
| Tables | 2 |
| Mathematics | 1 |
| Art/Photos/Cartoons | 1 |
| Maps | 1 |

Figure: `manuscript/figures/fig2_diagram_types.png`.

## 3. Source licences

All 30 figures are openly licensed. Twenty-eight come from third-party open
sources; the two mathematics-and-CS complex figures (loss landscape, LCS table)
are rendered locally and released by the author under CC-BY-4.0.

| Licence | Count |
|---|---|
| Public Domain | 17 |
| CC-BY-SA-3.0 | 8 |
| CC-BY-SA-4.0 | 2 |
| CC-BY-4.0 (local render) | 2 |
| CC-BY-3.0 | 1 |

Figure: `manuscript/figures/fig3_licences.png`.

## 4. Short-alt compliance with the DIAGRAM 125-character bound

The four decorative figures carry an empty short alt by design (correct WCAG
handling of decorative images). The 26 non-decorative figures have short alts
ranging from 17 to 53 characters (median 31.5), all within the DIAGRAM A.3
125-character bound. The corpus respects its own compliance claim:
`short_alt_violations` is empty.

Figure: `manuscript/figures/fig4_short_alt_length.png`.

## 5. Evaluation framework

The manuscript's Evaluation section defines four figures, produced by
`generate_eval_figures.py` from the held-out report:

1. **Convergence curve** — C-H Krippendorff alpha against DPO round, with the
   0.70 sustained-for-two-rounds threshold.
2. **Critic-human scatter** — per-figure critic vs human primary-outcome score
   on the held-out split, against the perfect-agreement diagonal.
3. **Per-dimension agreement** — C-H alpha for each of D1..D5 at the final
   round.
4. **Residual-disagreement heatmap** — mean absolute C-H difference by domain
   and category, to localise where the critic still diverges.

The renderers consume the report emitted by `pipeline/05_evaluate.py` and are
covered by `code/tests/test_eval_figures.py`.

**Demo preview (synthetic, not a result).** Before the real study runs, the four
figures can be previewed from a clearly labelled synthetic report. Run
`python code/scripts/generate_synthetic_ratings.py`, then render
`demo/held_out_report_SIMULATED.json` into `demo/figures/` (see
[`../demo/README.md`](../demo/README.md)). The preview exercises the renderer
only; the report carries a `_SYNTHETIC` banner and its numbers are not findings.

## Running the full study

The pipeline runs in order. Step 3 collects the two human ratings per figure;
the surrounding steps are mechanical. The run needs generator API keys
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`) and a GPU for the
open-weights generator, the critic, and the DPO trainer.

```bash
cd code
uv run python pipeline/01_build_corpus.py            # acquire/validate images, splits
uv run python pipeline/02_run_loop.py generator=gpt4o   # G-C loop -> loop_traces/
uv run python pipeline/03_collect_human_ratings.py   # H1 (domain expert) + H2 (screen-reader user)
uv run python pipeline/04_train_dpo.py training=dpo  # -> dpo/round_NN/ checkpoints
uv run python pipeline/05_evaluate.py                # -> held_out_report.json + alpha history
python analysis/generate_eval_figures.py --report outputs/<run>/held_out_report.json
```

## Reproducibility

```bash
cd "Academic Ops/ETH/digital accessibility/project work"
python analysis/analyze_corpus.py             # corpus figures + CSVs + summary
python analysis/make_publication_tables.py    # pubtab Excel inputs -> booktabs LaTeX
python analysis/make_publication_figure.py    # pubfig Nature-spec supplementary figure
```

Descriptive dependencies (`pandas`, `matplotlib`, `numpy`) are in the runtime
stack; the publication artefacts use the `analysis` optional group
(`uv pip install -e "code[analysis]"`: `pubtab`, `pubfig`, `openpyxl`).
