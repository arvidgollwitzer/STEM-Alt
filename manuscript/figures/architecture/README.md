# Architecture overview figure — STEM-Alt

PaperBanana-generated system-overview diagrams for the STEM-Alt generator–critic–human loop.

## Selected

**`cand_4.png`** — the manuscript system-overview figure. Chosen for the
cleanest left-to-right three-stage flow (Corpus → Nested Loops → Convergence & Output),
an explicit frozen/trainable legend, and the convergence threshold shown correctly as a
*criterion* (Krippendorff's α ≥ 0.7), not as an achieved result.

**Deployed:** copied to `../fig_overview.png` (the `\graphicspath` location) and rendered by
`paper/stem-alt.tex` as Figure 1 (`\ref{fig:overview}`, page 3). To swap the deployed
figure, copy a different candidate over `../fig_overview.png` and rebuild with `paper/build.sh`.

## Candidates

| File | Notes |
|------|-------|
| `cand_4.png` | ✅ **selected** — three-column flow + legend |
| `cand_1.png` | Nature a/b/c panels + explicit D1–D5 rubric list |
| `cand_2.png` | titled banner + legend, denser |
| `cand_3.png` | labelled loops + legend |
| `smoke.png`  | first pipeline test (1 critic round) |

## Provenance

- Engine: PaperBanana (Retriever → Planner → Stylist → Visualizer → Critic), `demo_full` mode.
- Models: `gemini-3.1-pro-preview` (reasoning) + `gemini-3.1-flash-image-preview` (image).
- Settings: 3 critic rounds, `retrieval=auto` (grounded in 610 PaperBananaBench references), 16:9.
- Generated: 2026-06-04.
- Reproducible inputs: `method.txt` (figure content) and `caption.txt` (visual intent + Nature style spec).

## Known limitation

Native resolution is **1376×768 px** (~200 DPI at double-column width) — fine for
review/draft, below the 300 DPI print spec. The image model is raster-only; true
print quality would require vector regeneration.
