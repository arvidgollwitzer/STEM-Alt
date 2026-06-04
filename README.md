[![Code: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![Data & manuscript: CC BY 4.0](https://img.shields.io/badge/Data%20%26%20manuscript-CC--BY--4.0-lightgrey.svg)](docs/DATA_RELEASE.md)
[![Course: ETH 376-1230-00L](https://img.shields.io/badge/ETH%20Z%C3%BCrich-376--1230--00L%20Digital%20Accessibility-b30000.svg)](Final%20Project%20Description.md)

# STEM-Alt: An Adversarial Generator–Critic Loop with Human-Aligned Review for STEM Alt-Text

Multimodal large language models draft alternative text for images at scale, but on scientific figures they fail in ways the affected reader cannot verify. We introduce the generator–critic–human loop, where a small set of human alt-text ratings is converted into a fine-tuned open-weights vision–language critic that approximates human judgement on STEM alt-text scoring, so the long tail of figures can be checked with sparse human oversight rather than rated one by one. We demonstrate a reproducible, born-accessible alternative to single-shot multimodal-LLM alt-text and to static benchmarks that measure the verification gap but do not close it.

Described by Gollwitzer (2026); the 6-page paper is in [`paper/stem-alt.pdf`](paper/stem-alt.pdf) (LaTeX source [`paper/stem-alt.tex`](paper/stem-alt.tex)).

**STEM-Alt's reproducibility guarantee belongs to its open-weights critic — LLaVA-Next-7B with rank-16 LoRA adapters — which fine-tunes with Direct Preference Optimization on a single GPU.** The three closed-API generators (GPT-4o, Claude 3.7 Sonnet, Gemini 2.5 Pro) need API keys; when you do NOT have them, the open-weights generator (LLaVA-Next-7B) runs the same loop offline on a GPU, and the pipeline runs end-to-end on test doubles with no GPU and no keys at all. STEM-Alt is developed and tested with Python 3.11 and `uv`.

![Figure 1. Overview of the STEM-Alt human-aligned self-correction loop: a corpus of 150 openly licensed STEM figures is partitioned into a calibration split and a held-out split; in the inner loop a generator drafts alt-text, the open-weights critic scores it on a five-dimension rubric and returns a critique, and the generator revises; on the calibration split a domain expert and a screen-reader user rate the final alt-text; in the outer loop the critic is fine-tuned with Direct Preference Optimization until critic–human Krippendorff's alpha reaches the pre-registered convergence target on the held-out split; the released artefact is the calibrated open-weights critic.](manuscript/figures/fig_overview.png)

*Figure 1. The STEM-Alt generator–critic–human loop. The base critic is frozen; only the LoRA adapters are trainable. The α ≥ 0.70 convergence criterion is a pre-registered target evaluated on the held-out split.*

## Table of Contents
- [Installation & General usage](#install)
- [Use Cases](#usecases)
- [Key Idea](#idea)
- [Benefits of STEM-Alt](#results)
- [Using STEM-Alt](#usage)
- [Directory Structure](#directory)
- [Licence](#licence)
- [Getting help](#contact)
- [Citing STEM-Alt](#cite)

## <a name="install"></a>Installation & General usage
```sh
git clone https://github.com/arvidgollwitzer/STEM-Alt
cd STEM-Alt/code

uv sync                          # install the stem_alt package + pipeline deps
uv sync --extra dev              # + test toolchain (pytest, ruff, mypy)
uv sync --extra accessibility    # + axe-core + Playwright for the release linter

# Run any of the six pipeline stages (each reads/writes the shared run directory):
uv run python pipeline/01_build_corpus.py              # validate corpus + write splits
uv run python pipeline/02_run_loop.py generator=gpt4o  # generator–critic loop
uv run python pipeline/03_collect_human_ratings.py     # rating sheets <-> JSONL ledger
uv run python pipeline/04_train_dpo.py training=dpo    # DPO-fine-tune the critic's LoRA
uv run python pipeline/05_evaluate.py                  # held-out convergence report
uv run python pipeline/06_release_artefacts.py         # born-accessible release bundle

uv run pytest -ra                # run the test suite (integration tests gated, off by default)
```
The paper itself builds separately: `./paper/build.sh` writes [`paper/stem-alt.pdf`](paper/stem-alt.pdf), and `./code/scripts/build_pdfs.sh` writes the accessible-summary PDF. See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the full reproduction protocol, including the human-rating pause points.

## <a name="usecases"></a>Use Cases
```sh
# GPT-4o generator (needs OPENAI_API_KEY)
uv run python pipeline/02_run_loop.py generator=gpt4o

# Claude 3.7 Sonnet generator (needs ANTHROPIC_API_KEY)
uv run python pipeline/02_run_loop.py generator=claude

# Gemini 2.5 Pro generator (needs GOOGLE_API_KEY)
uv run python pipeline/02_run_loop.py generator=gemini

# Open-weights generator, LLaVA-Next-7B — same loop, no API key (needs a GPU)
uv run python pipeline/02_run_loop.py generator=llava_next

# Sweep without code edits — Hydra composes conf/<group>/<name>.yaml at startup
uv run python pipeline/02_run_loop.py generator=gpt4o critic.lora_rank=16 loop.max_rounds=5

# Preview the pipeline on SYNTHETIC demo data — no GPU, no API keys; illustrative, not a result.
python code/scripts/generate_synthetic_ratings.py     # writes ratings_SIMULATED.jsonl + demo report
```
The synthetic preview writes a clearly labelled [`data/ratings/ratings_SIMULATED.jsonl`](data/ratings/ratings_SIMULATED.jsonl) and `demo/held_out_report_SIMULATED.json`, then renders the four evaluation figures into `demo/figures/`. See [`demo/README.md`](demo/README.md).

## <a name="idea"></a>The Key Idea
The bottleneck in accessible STEM teaching is human review. Human-rated alt-text is the gold standard, but no human team rates every figure in every course every semester, and static benchmarks measure the gap without closing it. Our goal is to amortise human judgement: teach an AI critic to score alt-text the way a human would on a small dual-rated calibration set, then let that calibrated critic steer AI generation across the long tail of figures with sparse human oversight.

STEM-Alt is based on five major ideas.
1. **Calibrate, then delegate.** A 120-figure calibration set with dual human ratings teaches a critic C to approximate human scoring; C then supervises generation on figures no human has rated.
2. **An adversarial generator–critic loop.** A generator G drafts alt-text under a WCAG-aware prompt; C scores it on five dimensions and returns a short critique; G revises; the pair iterates for k = 5 inner rounds or until C's score plateaus. The five dimensions are **factual correctness**, **information sufficiency**, **domain accuracy**, **hallucination**, and **conciseness**, each on a 1–5 Likert scale (primary outcome = mean of the first three).
3. **Direct Preference Optimization from (critic, human) pairs.** Accumulated (C-score, H-score) pairs become preference pairs; DPO fine-tunes C toward agreement with H. DPO is sample-efficient on a small preference set (≈2,400 pairs) and needs no separate reward model.
4. **Reproducibility belongs to the open-weights critic.** Closed-API generator outputs drift across versions, so they are logged and snapshotted into the loop trace; the re-runnable artefact is the open-weights LLaVA-Next-7B + LoRA checkpoint.
5. **Compliance is gated, not aspired.** An automated DIAGRAM linter rejects non-compliant gold descriptions at corpus-build time; human raters reject non-compliant loop output at rating time. Compliance failure is a generation error, not a rating dimension.

```
   one STEM figure
        │
        ▼
   Generator G  ──draft──▶  Critic C  ──5-dim score + 1-paragraph critique──┐
   (GPT-4o /                (LLaVA-Next-7B,                                  │
    Claude 3.7 Sonnet /      rank-16 LoRA adapters)                          │
    Gemini 2.5 Pro)  ◀───────────────── revise ──────────────────────────────┘
        │
        │  k = 5 inner rounds per figure, or until C's score plateaus
        ▼
   final alt-text  ──▶  Human H  (domain expert + screen-reader user via NVDA)
                        rates the same 5 dimensions — calibration split only
        │
        │  accumulate (C-score, H-score) pairs;  DPO every R = 30 figures
        ▼
   DPO fine-tunes C's LoRA adapters toward agreement with H
        │
        ▼
   held-out 30-figure split  ──▶  Krippendorff α(C, H) ≥ 0.70,
                                   sustained over two consecutive rounds
                                   └── pre-registered convergence target
```

## <a name="results"></a>Benefits of STEM-Alt
STEM-Alt closes the verification gap that single-shot multimodal alt-text leaves open. A 120-figure calibration set with dual human ratings teaches the critic to score alt-text the way a domain expert and a screen-reader user do, and the calibrated critic then steers generation across the long tail of figures with sparse human oversight instead of per-figure review. The convergence criterion is sharp and falsifiable: critic–human Krippendorff α **≥ 0.70** on the primary outcome — the mean of factual correctness, information sufficiency, and domain accuracy — **sustained across two consecutive DPO rounds**, on a held-out split that spans unseen subjects, unseen DIAGRAM image categories, and unseen STEM domains. A rating-quality floor of inter-rater α **≥ 0.60** gates every figure before it enters calibration, so the critic is aligned against human agreement that is itself reliable. The held-out evaluation set is still relatively small — 30 figures — so convergence is reported with figure-stratified bootstrap 95% confidence intervals (B = 2,000 resamples) and against the human inter-rater ceiling, and the set is being expanded.

The framework is fast, reproducible, and accessible by construction. DPO on ≈2,400 preference pairs with rank-16 LoRA on a frozen LLaVA-Next-7B fine-tunes the critic on a single GPU, with no separate reward model to fit. Reproducibility belongs to the open-weights critic: closed-API generator outputs are logged and snapshotted into the loop trace, and the fine-tuned LoRA checkpoint is the re-runnable surface that survives API drift. Every released artefact — the paper, the accessible summary, and the code documentation — is born-accessible: the PDFs target PDF/UA, are validated against the DIAGRAM Image Description Guidelines and WCAG 2.2 Success Criterion 1.1.1, and pass the PAC checker before publication. Compliance is gated, not aspired: an automated DIAGRAM linter rejects any non-compliant description at corpus-build time and human raters reject it at rating time, so a compliance failure is a generation error rather than a rating dimension.

## <a name="usage"></a>Using STEM-Alt:
The generator–critic–human loop can be implemented in different ways. We provide one well-optimised, config-driven implementation as a **six-stage procedure**: corpus build, generator–critic loop, human rating, DPO fine-tuning, held-out evaluation, and born-accessible release. These stages can be run individually or collectively depending on the target use; from stage 2 onward they share a single `LoopRecord` trace per figure as the source of truth.

| Stage | Script | Reads | Writes |
|---|---|---|---|
| 1 | `01_build_corpus.py` | `manifest.csv` | `splits.json` |
| 2 | `02_run_loop.py` | calibration split | `loop_traces/<figure_id>.json` |
| 3 | `03_collect_human_ratings.py` | loop traces | `ratings_*.jsonl` |
| 4 | `04_train_dpo.py` | loop traces + ratings | `dpo/round_NN/`, updated critic cfg |
| 5 | `05_evaluate.py` | held-out split + held-out ratings | `held_out_report.json` |
| 6 | `06_release_artefacts.py` | everything above | born-accessible bundle + WCAG check |

Each submodule under `code/src/stem_alt/` exposes a `<Type>Factory` lookup and a `register_<type>(name)` decorator, so adding a new generator, critic, trainer, or compliance rule is a one-file change with no edit to the factory wiring. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## <a name="directory"></a>Directory Structure:
```
STEM-Alt
├───1. paper
├───2. manuscript
├───3. code
├───4. data
├───5. analysis
├───6. docs
└───7. demo
```
1. The paper as LaTeX source (`stem-alt.tex`, Springer Nature template) and rendered `stem-alt.pdf`, the plain-language `accessible-summary.md` (rendered to PDF by `./code/scripts/build_pdfs.sh`), and the LaTeX bibliography `references.bib`. The paper builds with `./paper/build.sh`.
2. Supporting material the paper draws on: the corpus characterisation figures (`figures/`, with their underlying `figures/data/*.csv`), the table sources and data (`tables/*.tex`, `*.xlsx`, `*.md`), and the canonical verification-stamped bibliography `references.bib`.
3. Installable Python package `stem_alt`, the six-stage Hydra pipeline (`pipeline/`), the Hydra config groups (`conf/`), the helper scripts (`scripts/`), and the pytest suites (`tests/`). This is the reference implementation; it is config-driven and follows the Factory/Registry pattern throughout.
4. Corpus manifest (`corpus/manifest.csv`), the frozen calibration/held-out split (`splits.json`), and the five-dimension rating rubric (`ratings/rubric.yaml`). The held-out 30-figure subset plus metadata is the primary external evaluation surface.
5. Scripts that produce the manuscript figures and tables (`analyze_corpus.py`, `generate_eval_figures.py`, `make_publication_figure.py`, `make_publication_tables.py`).
6. Architecture map, the reproducibility and seed/provenance contract, the human-rating protocol, the compliance notes, and the data-release statement.
7. Clearly labelled **synthetic** fixtures: a simulated ratings ledger and held-out report, plus the four evaluation figures rendered from them. They let you exercise the pipeline and the figure renderer before the real study runs. See [`demo/README.md`](demo/README.md).

## <a name="licence"></a>Licence
The reference implementation (`code/`, `analysis/`, build scripts) is released under the **MIT** licence ([`LICENSE`](LICENSE)). The manuscript, accessible summary, 30-figure held-out corpus, and rubric are released under **CC-BY 4.0**; the calibrated critic LoRA checkpoint is released in this repository (the rank-16 LoRA adapter is versioned with Git LFS or attached as a release asset). Third-party corpus figures retain their original source licence, recorded per row in [`data/corpus/manifest.csv`](data/corpus/manifest.csv). See [`docs/DATA_RELEASE.md`](docs/DATA_RELEASE.md) for the full asset-by-asset breakdown and the figure-withdrawal procedure.

## <a name="contact"></a>Getting Help
If you have any suggestion for improvement, new applications, or collaboration, please contact arvidg at mit dot edu.
If you encounter bugs or have further questions or requests, you can raise an issue at the [issue page][issue].

## <a name="cite"></a>Citing STEM-Alt

If you use STEM-Alt in your work, please cite it (machine-readable metadata is in [`CITATION.cff`](CITATION.cff)):

> Arvid E. Gollwitzer.
> "STEM-Alt: An Adversarial Generator–Critic Loop with Human-Aligned Review for STEM Alt-Text."
> (2026). ETH Zürich, 376-1230-00L Digital Accessibility, FS2026.

Below is bibtex format for citation.

```bibtex
@misc{gollwitzer2026stemalt,
  author = {Arvid E. Gollwitzer},
  title  = {{STEM-Alt}: An Adversarial Generator--Critic Loop with
            Human-Aligned Review for {STEM} Alt-Text},
  year   = {2026},
  note   = {ETH Z\"urich, 376-1230-00L Digital Accessibility, FS2026},
  url    = {https://github.com/arvidgollwitzer/STEM-Alt},
}
```

[issue]: https://github.com/arvidgollwitzer/STEM-Alt/issues
