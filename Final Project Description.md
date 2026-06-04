# Final Project Description

**Course.** 376-1230-00L Digital Accessibility, ETH Zürich, FS2026

---

## Group members

- Arvid E. Gollwitzer (arvidg@mit.edu)

## Project title

STEM-Alt: An Adversarial Generator–Critic Loop with Human-Aligned Review for STEM Alt-Text.

## Short description

Multimodal LLMs are great at drafting alt-text faster than humans, but Lecture 12 argues they fail on complex scientific content, and the affected user cannot verify what they cannot see. We propose STEM-Alt to address the verification gap with a generator–critic–human loop.

A generator model G drafts alt-text for a STEM figure. A separate critic model C, acting adversarially, scores G's output on five dimensions: factual correctness, information sufficiency, domain accuracy, hallucination, conciseness. G revises against C's feedback; C re-scores; the pair iterates for k rounds. A human reviewer H rates the final alt-text independently on the same five dimensions. Across rounds and across figures, we collect (C-score, H-score) pairs and use them as the reward signal to fine-tune C with Direct Preference Optimization (DPO). The fine-tuning target is C's agreement with H.

Two convergence claims are tested. First, C–H disagreement (Krippendorff α and mean absolute score difference) decreases monotonically across fine-tuning rounds. Second, after k* rounds, C agrees with H within a pre-registered tolerance, and the loop can run with sparse human oversight.

The pipeline is exercised on 150 openly licensed STEM figures across chemistry, mathematics and CS, biology, and physics, stratified by the four ETH alt-text categories (simple, linked, decorative, complex) [1], [2]. The generator is chosen from {GPT-4o, Claude 3.7 Sonnet, Gemini 2.5 Pro}; the critic is an open-weights vision-language model (LLaVA-Next-7B with LoRA adapters), chosen so that DPO updates remain tractable on a single GPU.

Every gold-standard description and every loop output complies with the DIAGRAM Image Description Guidelines [3] and the DIAGRAM Accessible Image Sample Book [4].

### References

[1] ETH Zurich, "Text alternatives," *ETH Staffnet — Accessibility and Inclusion in Teaching*. https://ethz.ch/staffnet/en/teaching/accessibility-and-inclusion-in-teaching/accessibility-concepts/text-alternatives.html

[2] ETH Zurich, "Complex illustrations: Examples," *ETH Staffnet — Accessibility and Inclusion in Teaching*. https://ethz.ch/staffnet/en/teaching/accessibility-and-inclusion-in-teaching/accessibility-concepts/text-alternatives/complex-illustrations-examples.html

[3] DIAGRAM Center and National Center for Accessible Media (NCAM), "Image description guidelines," Benetech, 2019. [Online]. Available: http://diagramcenter.org/table-of-contents-2.html

[4] DIAGRAM Center, "Accessible image sample book," Benetech, 2019. http://diagramcenter.org/standards-and-practices/accessible-image-sample-book.html

## Goal agreement

- Release 30 STEM figures with metadata, stratified by the four ETH alt-text categories and four STEM domains.
- Produce ~10 representative examples of model-generated alt-text from three multimodal systems under two prompting regimes (900 candidates), with prompts, model versions, decoding parameters, and timestamps logged.
- Rate every candidate: primary-outcome target α ≥ 0.6.
- Quantify failure modes by domain, category, and rubric dimension with effect sizes.
- Identify cases where AI introduces information that misleads a screen-reader user, and propose concrete mitigations.

**Deliverables.** 10-minute presentation, 6-page paper, 1 to 2 page accessible PDF summary, public GitHub repo with critic LoRA checkpoint.
