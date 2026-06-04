# Compliance

The automated linter rejects any gold-standard description that fails the DIAGRAM rules at corpus build time, and the WCAG validator rejects any release HTML that fails SC 1.1.1 at release-bundle time.

## Standards

- **WCAG 2.2 Success Criterion 1.1.1** — non-text content carries a text
alternative.
- **DIAGRAM Image Description Guidelines** (Benetech, 2019).
- **DIAGRAM Accessible Image Sample Book** (Benetech, 2019).
- **ETH staffnet four-category alt-text taxonomy** (simple, linked,
decorative, complex).
- **PDF/UA** for tagged PDF builds.
- **EPUB Accessibility 1.1** for the EPUB build.

## Where each rule is enforced


| Rule source                        | Enforced by                                                   | When                                                   |
| ---------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------ |
| DIAGRAM general rules              | `compliance/diagram_linter.py`                                | corpus build, every loop output                        |
| WCAG SC 1.1.1                      | `compliance/wcag_validator.py`                                | release bundle build                                   |
| ETH four-category taxonomy         | `compliance/eth_categories.py`                                | corpus row validation; generator prompt classification |
| PDF/UA tagging                     | Pandoc + tagged-PDF post-processor in `scripts/build_pdfs.sh` | release                                                |
| axe-core HTML audit                | external tool invoked from the release pipeline               | release                                                |
| Ace by DAISY                       | external tool invoked from the release pipeline               | release (EPUB only)                                    |
| PAC (PDF/UA Accessibility Checker) | external tool invoked from the release pipeline               | release (PDF only)                                     |


## DIAGRAM general rule checklist


| #   | Rule                | Linter check                                                                                                                                                             |
| --- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Context is key      | The manifest must carry a non-empty `context_paragraph`.                                                                                                                 |
| 2   | Audience-aware      | Audience fixed at "blind or low-vision STEM reader, undergraduate to research level"; descriptions are checked for jargon density relative to the figure's DIAGRAM type. |
| 3   | Be concise          | Short alt ≤ 125 characters where the image type permits.                                                                                                                 |
| 4   | Be objective        | The linter flags pedagogical phrasing ("this teaches", "the goal of this figure").                                                                                       |
| 5   | General to specific | Every long description opens with a one-sentence summary; the opener is checked for length.                                                                              |
| 6   | Tone                | Passive constructions in long descriptions are flagged.                                                                                                                  |
| 7   | Inset handling      | Insets that are graphs are required to be rendered as row-and-column tables in the long description (manually reviewed; not auto-linted).                                |


## Release-time WCAG validation

`pipeline/06_release_artefacts.py` parses every `<img>` in the release
HTML, builds a `FigureRecord`, and runs `WCAGValidator.validate`. Any
violation aborts the release. The categories:

- Decorative images must declare `alt=""`.
- Informative images must carry a non-empty `alt`.
- Complex images must reference a long description via
`aria-describedby`.

## Born-accessible build artefacts

The tagged **PDF is the primary born-accessible artefact**; the HTML and
EPUB renderings are optional and produced from the same sources by the
release pipeline when requested.


| Build         | Tool                                        | Verifies against       | Status   |
| ------------- | ------------------------------------------- | ---------------------- | -------- |
| PDF (paper)   | `pdflatex` + SN template (`paper/build.sh`) | PDF/UA                 | primary  |
| PDF (summary) | Pandoc → LaTeX (`scripts/build_pdfs.sh`)    | PDF/UA                 | primary  |
| HTML          | release pipeline + `axe-core`               | WCAG 2.2 AA            | optional |
| EPUB          | Pandoc → EPUB3 + Ace by DAISY               | EPUB Accessibility 1.1 | optional |


