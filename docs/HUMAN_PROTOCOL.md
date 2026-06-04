# Human-in-the-loop protocol

## Recruitment

Two raters per calibration figure:

1. **Domain expert.** Research-level fluency in the figure's STEM area.
  Recruited through ETH and MIT contacts; identification verified via
   institutional email or ORCID.
2. **Screen-reader user.** Primary path: Stiftung Zugang f&uuml;r alle.
  Backup: remote rater via the WAI community channels. Disclosed
   fallback: sighted rater with documented screen-reader experience.

Every rating record stores the rater's role in `rater_role`. The held-out
evaluation reports fallback ratings separately; they do not contribute to
the headline Krippendorff α.

## Rating session

1. The rater receives a sheet containing the figure, the surrounding
  context paragraph, the DIAGRAM figure type, and the candidate
   alt-text. The rater does not see the critic's scores or the
   generator's identity.
2. Screen-reader-user raters listen to the alt-text rendered with NVDA at
  standard rate (live mode) or to a pre-rendered WAV file (offline mode,
   produced by `stem_alt.human.NVDARenderer`).
3. The rater scores each dimension 1–5 (Likert) and writes a one-paragraph
  critique. Scores below 3 require at least one supporting sentence in
   the critique.
4. The session records timestamp, rater id, rater role, and the
  `rendered_via_nvda` flag.

## Blinding

- Critic scores are hidden from raters.
- Generator identity is hidden from raters.
- Round index is hidden from raters (the candidate is shown without
"round k of 5" labelling).

## Rubric freeze

The five-dimension rubric is piloted on 20 figures, adjudicated between
rater pairs, and frozen before scaling. Any edit after the freeze is
recorded as a protocol deviation in the limitations section.

## Pilot adjudication

For each pilot figure:

1. Two raters score independently.
2. Differences ≥ 2 points on any dimension are flagged.
3. The flagged pair adjudicates with the project lead present; the
  rubric definition is sharpened if the disagreement reveals an
   ambiguity in the rubric (not in the figure).
4. After adjudication, the rubric is frozen and `rubric.yaml` is
  committed. No further rubric edits are permitted.

## Inter-rater agreement reporting

Headline statistics report:

- H1–H2 Krippendorff's α — pre-registered rating-quality floor at **α ≥ 0.60**
on the primary outcome (mean of D1, D2, D3). Matches the FPD goal agreement.
Figures below the floor are adjudicated. If adjudication does not recover
them, they leave the calibration set and the exclusion is reported.
- C–H Krippendorff's α — pre-registered convergence threshold at **α ≥ 0.70**
on the primary outcome, **sustained across two consecutive DPO rounds** on
the held-out split (paper §3.5, §4).
- The gap between them, which bounds how much further the critic can be  
pushed by additional DPO data without a richer rubric.

