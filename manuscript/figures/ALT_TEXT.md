# Alt Text for Figures

Text alternatives for the corpus-characterisation charts in this folder, written to the
DIAGRAM Image Description Guidelines and WCAG 2.2 Success Criterion 1.1.1. Each chart is a
data graphic, so the alt text opens with the chart type and then reports the values it shows.
Values match the backing tables in [`data/`](data/) and `corpus_summary.json`.

## fig_overview.png
Schematic pipeline diagram of the STEM-Alt human-aligned self-correction loop, read left to right, and used as Figure 1 of the paper and the README hero. A corpus of 150 openly licensed STEM figures, stratified by domain and ETH category, is partitioned into a 120-figure calibration split and a 30-figure held-out split. In the inner loop a generator G (GPT-4o, Claude 3.7 Sonnet, or Gemini 2.5 Pro) drafts a candidate alt-text, the open-weights critic C (LLaVA-Next-7B with rank-16 LoRA adapters) scores it on the five-dimension rubric and returns a critique, and G revises, for k = 5 rounds or until the score plateaus. On the calibration split a human H (a domain expert and a screen-reader user listening through NVDA) rates the final alt-text on the same rubric. In the outer loop, every R = 30 figures the accumulated critic–human score pairs fine-tune C with Direct Preference Optimization. Training stops when the critic–human Krippendorff alpha reaches the pre-registered convergence criterion (alpha >= 0.70, sustained over two consecutive rounds) on the held-out split. The released artefact is the calibrated open-weights critic; the base model is frozen and only the LoRA adapters are trainable.

## fig1_stratification.png
Grouped bar chart of corpus stratification: number of figures (y axis) by STEM domain (x axis: Chemistry, Mathematics and computer science, Biology, Physics), with one bar per ETH category (simple, linked, decorative, complex). Chemistry and Mathematics and computer science hold 8 figures each (2 simple, 2 linked, 1 decorative, 3 complex); Biology and Physics hold 7 each (1 simple, 2 linked, 1 decorative, 3 complex). Total 30.

## fig2_diagram_types.png
Horizontal bar chart of the DIAGRAM figure-type distribution across the 30 figures: Graphs 8, Relational Diagrams 7, Photos 4, Illustrated Diagrams 4, Chemistry 2, Tables 2, Mathematics 1, Art/Photos/Cartoons 1, Maps 1.

## fig3_licences.png
Bar chart of the source-licence distribution across the 30 figures: public domain 17, CC-BY-SA-3.0 8, CC-BY-SA-4.0 2, CC-BY-4.0 2, CC-BY-3.0 1.

## fig4_short_alt_length.png
Histogram of short-alt length in characters for the non-decorative figures, with a dashed reference line at the DIAGRAM 125-character bound. Every short alt sits well below the bound (longest about 53 characters). The four decorative figures are excluded, as their alt is empty by design.

## fig_corpus_stratification_pub.png
Publication version of the corpus-stratification chart, showing the same data as `fig1_stratification.png`: a grouped bar chart of figure counts by STEM domain and ETH category, totalling 30. Released as PNG, PDF, and SVG (`fig_corpus_stratification_pub.pdf`, `fig_corpus_stratification_pub.svg`).
