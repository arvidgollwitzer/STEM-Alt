# Data release

We provide a Data Availability and FAIR-metadata record for STEM-Alt below. We map each dataset that supports the study to a location, a licence, and an access route.

## Data availability

The data supporting this study are the 30-figure held-out STEM-Alt corpus and its
metadata. The author-generated components — the manifest (`manifest.csv`), the frozen
split (`splits.json`), the five-dimension rubric (`rubric.yaml`), the expert reference
descriptions and short-alt text, and two locally rendered figures
(`mathcs_complex_loss_landscape.png` and `mathcs_complex_dynamic_programming.png`) —
are released under CC-BY 4.0 in the project repository
(`https://github.com/arvidgollwitzer/STEM-Alt`). The remaining 28 figures are reused
public images from Wikimedia Commons, OpenStax (CC-BY 4.0), MIT OpenCourseWare, and
arXiv (CC-BY 4.0); `manifest.csv` records each figure's source URL and licence, and
`pipeline/01_build_corpus.py` retrieves the image files from those sources. The
DPO-fine-tuned LLaVA-Next-7B LoRA checkpoint is released in the same repository
(large binaries are versioned with Git LFS or attached as a release asset). Human
ratings are collected under the protocol described in the paper and are not part of
this release. The synthetic fixtures under `demo/` and
`data/ratings/ratings_SIMULATED.jsonl` are simulated placeholders for pipeline
testing, not research data, and must not be cited as results.

## Assets and licences


| Asset                             | Licence                 | Notes                                                                                                           |
| --------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| 30-figure held-out corpus         | CC-BY 4.0 (aggregation) | Individual figures retain their source licence.                                                                 |
| Manifest, splits, rubric          | CC-BY 4.0               |                                                                                                                 |
| Calibrated critic LoRA checkpoint | CC-BY 4.0               | Released in this repository; the rank-16 LoRA adapter is versioned with Git LFS or attached as a release asset. |
| Reference implementation (code)   | MIT                     |                                                                                                                 |
| Paper, accessible summary         | CC-BY 4.0               |                                                                                                                 |


The aggregation licence covers the manifest and the author-generated metadata only.
The 28 third-party figures keep their own source licences, recorded per row in
`manifest.csv`; do not relicense them.

## Persistent identifier

All artefacts live in the single project repository,
`https://github.com/arvidgollwitzer/STEM-Alt`; large binaries (the critic checkpoint)
are versioned with Git LFS or attached as release assets. To make the release citable
with a persistent identifier without moving anything out of GitHub, archive the
repository to Zenodo through the built-in GitHub–Zenodo integration: each tagged
release is archived and minted a DOI. Record that DOI here, in `CITATION.cff`, and in
the paper's Data Availability statement.

## Citation

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

## Manifest schema

`manifest.csv` columns:


| Column                         | Type   | Notes                                                       |
| ------------------------------ | ------ | ----------------------------------------------------------- |
| `figure_id`                    | string | Unique snake_case identifier.                               |
| `source_url`                   | string | Original URL.                                               |
| `licence`                      | string | Source licence (CC-BY, CC-BY-SA, public domain, ...).       |
| `domain`                       | string | One of `chemistry`, `mathematics_cs`, `biology`, `physics`. |
| `eth_category`                 | string | One of `simple`, `linked`, `decorative`, `complex`.         |
| `diagram_type`                 | string | Per DIAGRAM Specific Guidelines taxonomy.                   |
| `expert_reference_description` | string | Gold-standard description.                                  |
| `short_alt`                    | string | Short alt attribute (≤ 125 chars for simple/linked).        |
| `context_paragraph`            | string | Surrounding paragraph from the source.                      |
| `image_path`                   | string | Path under `data/corpus/images/`.                           |
| `split`                        | string | `calibration` or `held_out`.                                |


## Provenance

- Author-generated metadata (reference descriptions, short alt, domain / ETH-category
/ DIAGRAM-type labels) were written and checked against the DIAGRAM guidelines and
the ETH taxonomy; the corpus build rejects any row that fails the DIAGRAM linter.
- The two locally rendered figures are produced deterministically (seeded) by
`code/scripts/render_local_figures.py` and carry CC-BY 4.0.
- For reused figures, the source URL is the access pointer; record an access date
when a source carries no stable version (Wikimedia files are pinned by file-page URL).

## Re-distribution

When redistributing the released corpus or the LoRA checkpoint:

1. Keep the per-figure source attribution intact.
2. Preserve the CC-BY notice on the aggregated manifest.
3. State any modifications you make to the rubric.
4. Cite the paper.

## Removing a figure

If a figure's original licence is challenged or revoked:

1. Remove the row from `manifest.csv`.
2. Re-run `pipeline/01_build_corpus.py` to update `splits.json`.
3. Mark the figure id as `withdrawn:<reason>:<date>` in a `WITHDRAWALS.md`
  file alongside the manifest.
4. Re-run the release pipeline.

The critic LoRA checkpoint is never edited retroactively. The next
fine-tuning round on the reduced corpus replaces it.