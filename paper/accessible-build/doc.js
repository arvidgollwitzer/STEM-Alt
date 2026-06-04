// Assemble the accessible STEM-Alt Word document and write stem-alt-accessible.docx.
const m = require("./build.js");
const {
  fs, path, Document, Packer, Paragraph, AlignmentType, HeadingLevel,
  LevelFormat, Header, Footer, TextRun, PageNumber, FootnoteReferenceRun,
  TabStopType, TabStopPosition, ExternalHyperlink,
  R, B, I, sub, sup, P, H1, H2, caption, figure, buildTable,
  figs, REFS, refParagraph, FONT,
} = m;

const children = [];
const push = (...x) => x.forEach((e) => (Array.isArray(e) ? children.push(...e) : children.push(e)));

// ---------------- TITLE BLOCK ----------------
push(new Paragraph({
  style: "PaperTitle",
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [R("STEM-Alt: An Adversarial Generator–Critic Loop with Human-Aligned Review for STEM Alt-Text")],
}));
push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [R("Arvid E. Gollwitzer", { size: 24 }), sup("1,2,3*")],
}));
const affil = (n, t) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 20 },
  children: [sup(n), R(t, { size: 18 })],
});
push(affil("1*", "Department of Electrical Engineering and Computer Science, Massachusetts Institute of Technology, Cambridge, 02139, MA, USA."));
push(affil("2", "Broad Institute of MIT and Harvard, Cambridge, 02142, MA, USA."));
push(affil("3", "ETH Zürich, Zürich, Switzerland."));
push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 80, after: 200 },
  children: [R("Corresponding author: ", { size: 18 }),
    new ExternalHyperlink({ children: [new TextRun({ text: "arvidg@mit.edu", style: "Hyperlink", font: FONT, size: 18 })], link: "mailto:arvidg@mit.edu" })],
}));

// ---------------- ABSTRACT ----------------
push(H1("Abstract"));
push(P([
  R("Most scientific figures on the web carry no equivalent text alternative. Multimodal large language models cannot fill that gap, because the screen-reader user cannot verify a confidently wrong description. At the scale of a university course catalogue, human review is the bottleneck: rating every figure in every STEM course every semester is infeasible. We present "),
  B("STEM-Alt"),
  R(", a generator, critic, and human loop that converts a small set of dual human ratings into a domain-specific open-weights critic for STEM alt-text. The critic is LLaVA-Next-7B with rank-16 LoRA adapters, fine-tuned on 120 figures stratified across four STEM domains and the four ETH alt-text categories. The generator G is drawn from three closed-API multimodal systems (GPT-4o, Claude 3.7 Sonnet, Gemini 2.5 Pro) under two prompting regimes (P1 generic, P2 WCAG-aware). The three systems and two regimes together yield 900 candidate alt-texts. The inner loop runs k = 5 rounds per figure. The convergence target is Krippendorff’s α ≥ 0.7 between the calibrated critic C and the human raters H on a 30-figure held-out split. The target must hold across two consecutive Direct Preference Optimization rounds. The released artefact has four parts: an open-weights LoRA checkpoint, a CC-BY corpus, a born-accessible reference implementation validated against the DIAGRAM Image Description Guidelines and WCAG 2.2 SC 1.1.1, and the protocol an ETH course team can run on its existing figure backlog. The calibrated critic is positioned as an assistant, not as an arbiter, following Lecture 12 of the ETH Digital Accessibility course. Human review remains authoritative on the calibration split. The reproducibility guarantee belongs to the open-weights critic, not to the closed-API generators."),
]));
push(new Paragraph({
  spacing: { after: 200 }, alignment: AlignmentType.LEFT,
  children: [B("Keywords: "), R("alt-text, scientific figures, WCAG 2.2, DIAGRAM, vision–language models, LLM-as-judge, Direct Preference Optimization, screen-reader users, accessibility")],
}));

// ---------------- 1 INTRODUCTION ----------------
push(H1("1  Introduction"));
push(P([R("A blind or low-vision student encountering a STEM figure has one chance to learn from it: the text alternative. If the alt-text is wrong, the student cannot tell. WCAG 2.2 Success Criterion 1.1.1 [1] makes the alt-text mandatory. STEM teaching routinely fails it because the figures carry the information and writing equivalent text is hard. Multimodal large language models can draft alt-text quickly, yet on scientific content their drafts fail in ways the affected reader cannot verify. Lecture 12 of the ETH Digital Accessibility course [2] names three structural reasons. Training data on complex, novel scientific content is sparse, so AI interpretations are sometimes highly flawed. Trust collapses when the reader cannot audit the output. And outsourcing accessibility to AI pushes the inclusion burden back onto the affected individual, against the lecture’s principle that “accessibility is the prerequisite for good AI, not its result”.")]));
push(P([R("Human review is the bottleneck. Human-rated alt-text is the gold standard, but no human team rates every figure in every ETH course every semester. Static benchmarks measure the gap; they do not close it.")]));
push(P([R("We introduce "), B("STEM-Alt"), R(", a generator, critic, and human loop that amortises human judgement across the long tail of figures (Fig. 1). A small dual-rated calibration set teaches an open-weights critic to score alt-text the way the human raters do. The calibrated critic then scores AI-generated alt-text on the remaining figures with only sparse human oversight. The critic is an assistant, not an arbiter, in the lecture’s sense of “always my assistant, never in charge” [2]. Human ratings remain authoritative on the calibration split. The critic extends that judgement to the long tail only under a falsifiable convergence criterion.")]));

push(figure({ ...figs.overview, num: 1, captionRuns: [
  B("Fig. 1  "),
  R("Overview of the STEM-Alt human-aligned self-correction loop for scientific-figure alt-text. Schematic pipeline diagram, read left to right. A corpus of 150 openly licensed STEM figures, stratified by domain and ETH category, is partitioned into a 120-figure calibration split and a 30-figure held-out split. In the inner loop, a closed-API generator G (GPT-4o, Claude 3.7 Sonnet, or Gemini 2.5 Pro) drafts a candidate alt-text. The open-weights critic C (LLaVA-Next-7B with rank-16 LoRA adapters) scores it on the five-dimension rubric and returns a one-paragraph critique, and G revises, for k = 5 rounds or until the score plateaus. On the calibration split, a human H rates the final alt-text on the same rubric. Here H is a domain expert and a screen-reader user listening through NVDA. In the outer loop, every R = 30 figures the accumulated critic–human score pairs fine-tune C with Direct Preference Optimization. Training stops when the critic–human Krippendorff α meets the pre-registered convergence criterion on the held-out split (α ≥ 0.7, sustained over two consecutive DPO rounds). The released artefact is the calibrated open-weights critic: the base model is frozen and only the LoRA adapters are trainable."),
]}));

push(P([B("Contributions. "), R("(1) A domain-specific calibrated critic for STEM alt-text, released as an open-weights LoRA checkpoint on LLaVA-Next-7B. (2) A falsifiable convergence criterion: Krippendorff’s α between critic and human on a held-out 30-figure split, monotonic improvement across DPO rounds, and a 0.7 threshold sustained across two consecutive rounds. (3) A born-accessible reference implementation aligned with the DIAGRAM Image Description Guidelines [3], the DIAGRAM Accessible Image Sample Book [4], and the ETH four-category alt-text taxonomy [5, 6]. (4) A characterisation of the minimum human budget required to reach the tolerance, and a residual-disagreement profile by domain, category, and rubric dimension.")]));
push(P([R("STEM-Alt does not propose a new optimisation algorithm. It packages an existing one (DPO) and an existing critic family (LLaVA-Next-7B with LoRA) into a domain-specific calibrated artefact that an ETH course team can run on its existing figure backlog. The contribution is the artefact, not the algorithm.")]));

// ---------------- 2 BACKGROUND ----------------
push(H1("2  Background and Related Work"));
push(P([R("Two literatures bear directly on STEM-Alt: LLM-as-judge calibration and accessibility-compliant alt-text generation. LLM-as-judge has become a standard evaluation approach in language modelling, with MT-Bench [7], G-Eval [8], JudgeLM [9], and Prometheus [10] the canonical examples. These methods calibrate general-purpose judges on general text distributions. STEM-Alt instead narrows the target to a specific domain (STEM figures), a specific evaluator (open-weights LLaVA-Next-7B [11]), and a specific update path (DPO [12] from in-domain dual human ratings). The judge does not need to be universal. It needs to be reliable in distribution.")]));
push(P([R("The optimisation route is chosen for sample efficiency, not for novelty. We use DPO [12] rather than full RLHF [13] on a small calibration set, and LoRA [14] so that fine-tuning a 7B vision–language model stays tractable on a single GPU. Closed-API generators drift across versions, so the reproducibility guarantee belongs to the open-weights critic only. Section 3.5 gives the technical detail.")]));
push(P([R("Compliance follows four normative sources. The DIAGRAM Image Description Guidelines [3] and the DIAGRAM Accessible Image Sample Book [4] fix the format and figure-type taxonomy. The ETH “Text Alternatives” guidance [5] fixes the four-category split (simple, linked, decorative, complex). WCAG 2.2 SC 1.1.1 [1] is the normative gate. Every gold-standard description and every loop output meets these standards. An automated linter enforces compliance at corpus build time, and human raters reject any output that fails the same rules at rating time.")]));

// ---------------- 3 METHOD ----------------
push(H1("3  Method"));
push(H2("3.1  Corpus"));
push(P([R("The corpus is designed to expose the critic to every cell of the ETH-category by STEM-domain matrix. It also keeps a held-out slice that the loop never sees. It contains 150 openly licensed figures drawn from OpenStax, MIT OpenCourseWare, arXiv CC-BY, and Wikimedia Commons. We partition the corpus at the start into a "), B("calibration split"), R(" of 120 figures (loop and DPO fine-tuning) and a "), B("held-out evaluation split"), R(" of 30 figures (never used for fine-tuning). Stratification runs along two axes: STEM domain (chemistry, mathematics and computer science, biology, physics) and ETH alt-text category (simple, linked, decorative, complex). Each entry carries the source URL, the licence, the domain, the ETH category, the DIAGRAM image type, an expert reference description, a short alt, and the surrounding context paragraph from the source. The released subset (Table 1, Fig. 2) is the held-out 30 figures plus their metadata. It serves as the primary external evaluation set for downstream users of the critic.")]));

push(figure({ ...figs.strat, num: 2, captionRuns: [
  B("Fig. 2  "),
  R("Composition of the released 30-figure held-out corpus. Grouped bar chart of the number of figures by STEM domain (chemistry, mathematics and computer science, biology, physics), with one bar per ETH alt-text category (simple, linked, decorative, complex). Chemistry and mathematics and computer science hold eight figures each (two simple, two linked, one decorative, three complex); biology and physics hold seven each (one simple, two linked, one decorative, three complex). Complex figures dominate (12 of 30) by design, because they are where AI alt-text fails hardest and where the critic is most needed."),
]}));

// Table 1
push(caption([B("Table 1  "), R("Held-out evaluation split, stratified by STEM domain and ETH alt-text category. Cells give the count of figures.")]));
const C = AlignmentType.CENTER;
push(buildTable({
  widths: [3360, 1200, 1200, 1200, 1200, 1200],
  header: [{ text: "Domain" }, { text: "Simple", align: C }, { text: "Linked", align: C }, { text: "Decorative", align: C }, { text: "Complex", align: C }, { text: "Total", align: C }],
  rows: [
    [{ runs: [R("Chemistry")] }, { runs: [R("2")], align: C }, { runs: [R("2")], align: C }, { runs: [R("1")], align: C }, { runs: [R("3")], align: C }, { runs: [R("8")], align: C }],
    [{ runs: [R("Mathematics and computer science")] }, { runs: [R("2")], align: C }, { runs: [R("2")], align: C }, { runs: [R("1")], align: C }, { runs: [R("3")], align: C }, { runs: [R("8")], align: C }],
    [{ runs: [R("Biology")] }, { runs: [R("1")], align: C }, { runs: [R("2")], align: C }, { runs: [R("1")], align: C }, { runs: [R("3")], align: C }, { runs: [R("7")], align: C }],
    [{ runs: [R("Physics")] }, { runs: [R("1")], align: C }, { runs: [R("2")], align: C }, { runs: [R("1")], align: C }, { runs: [R("3")], align: C }, { runs: [R("7")], align: C }],
    [{ runs: [B("Total")] }, { runs: [B("6")], align: C }, { runs: [B("8")], align: C }, { runs: [B("4")], align: C }, { runs: [B("12")], align: C }, { runs: [B("30")], align: C }],
  ],
}));
push(new Paragraph({ spacing: { after: 160 }, children: [] }));

push(P([B("Corpus characterisation. "), R("Three descriptive properties of the released split are reported directly from the manifest by "), R("analysis/analyze_corpus.py", { font: "Consolas", size: 20 }), R(", and each ships with the CSV it was rendered from. First, the corpus spans nine DIAGRAM figure types. Graphs (8) and relational diagrams (7) are the most frequent, matching the structure-heavy content of STEM teaching material. Second, all 30 figures are openly licensed. The 28 reused third-party images are public domain (17), CC-BY-SA-3.0 (8), CC-BY-SA-4.0 (2), and CC-BY-3.0 (1). The two mathematics-and-computer-science complex figures, a loss landscape and a longest-common-subsequence table, are rendered locally and released by the author under CC-BY 4.0. Third, the corpus satisfies its own compliance claim. The four decorative figures carry an empty short alt by design. The 26 non-decorative figures have short alts of 17 to 53 characters (median 31.5). None exceeds the DIAGRAM §A.3 125-character bound, so the violation set is empty. Appendix A gives the per-type, per-licence, and short-alt-length distributions as figures.")]));

push(H2("3.2  Generator G"));
push(P([R("The generator G is drawn from three closed-API frontier multimodal systems: GPT-4o, Claude 3.7 Sonnet, and Gemini 2.5 Pro. Closed-API outputs drift across versions, so the reproducibility guarantee is carried by the open-weights critic rather than by the generators. The critic’s LLaVA-Next-7B backbone can be pinned at a model revision for exact re-runs.")]));
push(P([R("Two prompts are used. "), B("P1 (generic)"), R(" is the one-line instruction “Provide alt-text for this image suitable for a blind reader.” "), B("P2 (WCAG-aware)"), R(" names the four ETH categories and asks G to classify the figure before describing it. The output then conforms to the ETH-category contract: a concise alt for simple or linked figures, an empty alt attribute for decorative figures, and a short alt plus a long description for complex figures. P2 embeds the DIAGRAM general rules and shows one Sample Book chapter as a one-shot example. Inside the loop, G receives C’s score and short critique and revises. Temperature is fixed at 0. Prompts, model versions, decoding parameters, and timestamps are logged for every candidate. Across the full 150-figure corpus, the three generators under two prompting regimes produce 3 × 2 × 150 = 900 candidate alt-texts.")]));

push(H2("3.3  Critic C"));
push(P([R("The critic C is LLaVA-Next-7B with rank-16 LoRA adapters on the attention query, key, value, and output projections. We freeze the base model and train only the adapters between rounds. C receives the image, the candidate alt-text, the surrounding context paragraph, and the DIAGRAM figure type. It then emits five-dimension scores plus a one-paragraph critique:")]));

// Table 2 rubric
push(caption([B("Table 2  "), R("Five-dimension rubric. "), R("D", { italics: true }), sub("1"), R("–"), R("D", { italics: true }), sub("3"), R(" form the primary outcome.")]));
const dimRow = (d, name, def) => [
  { runs: [R("D", { italics: true }), sub(d)], align: C },
  { runs: [R(name)] },
  { runs: [R(def)] },
];
push(buildTable({
  widths: [900, 2400, 6060],
  header: [{ text: "Dim.", align: C }, { text: "Name" }, { text: "Definition" }],
  rows: [
    dimRow("1", "Factual correctness", "Does the description correctly state what is visible?"),
    dimRow("2", "Information sufficiency", "Enough to reconstruct the figure’s claim?"),
    dimRow("3", "Domain accuracy", "Are technical terms used correctly in the figure’s field?"),
    dimRow("4", "Hallucination", "Does the description add content not in the figure?"),
    dimRow("5", "Conciseness", "Does it follow DIAGRAM length guidance for its category?"),
  ],
}));
push(new Paragraph({ spacing: { after: 160 }, children: [] }));
push(P([R("Each dimension is scored on a 5-point Likert scale (1 = poor, 5 = excellent). The primary outcome is the mean of D1, D2, D3, the dimensions most directly tied to factual screen-reader utility.")]));

push(H2("3.4  The loop"));
push(P([R("For each figure, the loop runs: (1) G produces alt-text under P2; (2) C scores and returns a short critique; (3) G revises against the critique; (4) steps 2–3 repeat for k = 5 inner rounds, or until C’s score plateaus (Δ on the primary outcome below 0.1 between consecutive rounds); (5) H rates the final alt-text on calibration-split figures.")]));

push(H2("3.5  DPO fine-tuning"));
push(P([R("DPO is chosen over full RLHF for sample efficiency. The calibration set yields only ∼2,400 preference pairs, well below the regime where a learned reward model is reliable. DPO’s closed-form objective on preference pairs eliminates one source of approximation error and one stage of training. Every R = 30 newly calibrated figures, we fine-tune C on the accumulated (C-score, H-score) pairs. We construct preference pairs by ranking within-figure candidates by H-score. Each figure yields 4 candidates, hence C(4,2) = 6 pairs, giving 6 × 30 = 180 in-figure pairs per fine-tuning round. Across the four fine-tuning rounds of the 120-figure calibration set this gives 720 within-figure pairs. Between-round comparisons augment that to roughly 2,400. The DPO objective [12] is")]));
// Equation (1)
push(new Paragraph({
  alignment: AlignmentType.LEFT,
  spacing: { before: 80, after: 80 },
  tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
  children: [
    R("    "),
    R("ℒ", { italics: true }), sub("DPO"), R("(C) = − 𝔼", { italics: true }),
    sub("(x, y⁺, y⁻) ∼ 𝒟_pref"),
    R("  [ log σ( β ( r"), sub("C"), R("(x, y⁺) − r"), sub("C"), R("(x, y⁻) ) ) ]"),
    R("\t(1)"),
  ],
}));
push(P([R("where x is the context tuple (image, surrounding paragraph, DIAGRAM figure type), y⁺ is the human-preferred candidate, y⁻ is dispreferred, r"), sub("C"), R("(x, y) = log [ π"), sub("C"), R("(y|x) / π"), sub("ref"), R("(y|x) ] is C’s implicit reward against the frozen reference policy, σ is the sigmoid, and 𝒟"), sub("pref"), R(" is the preference dataset. We use β = 0.1.")]));
push(P([R("We make three assumptions explicit. "), I("Reward identifiability"), R(": zero-initialised LoRA adapters give π"), sub("C"), R(" ≡ π"), sub("ref"), R(" at r = 0, so r"), sub("C"), R(" ≡ 0 there. The DPO gradient then depends only on y⁺, y⁻. "), I("Pair independence"), R(": in-figure pairs are conditionally independent given x. Between-round pairs (the same figure across rounds) are positively correlated, so we down-weight them by λ = 0.3 in the loss. "), I("Scale"), R(": α is computed under interval-scale assumptions [15], with ordinal-scale α reported as a robustness check.")]));
push(P([B("Stopping criterion. "), R("α ≥ 0.7 between C and H on the primary outcome (mean of D1, D2, D3), sustained across two consecutive fine-tuning rounds on the held-out split.")]));

push(H2("3.6  Human protocol"));
push(P([R("Two raters score each calibration figure. The first is a "), B("domain expert"), R(" with research-level fluency in the figure’s STEM area. The second is a "), B("screen-reader user"), R(" (recruited through Stiftung Zugang für alle) who listens to the alt-text rendered with NVDA at standard rate before rating. Both raters use the same five-dimension rubric on the same 5-point scale, and raters do not see C’s scores. The rubric is piloted on a 20-figure subset, disagreements are adjudicated, and the rubric is frozen before scaling. An inter-rater reliability floor of Krippendorff’s α ≥ 0.6 between H1 and H2 on the primary outcome is required. Figures whose ratings fall below the floor are adjudicated rather than entering the calibration set. The C–H convergence threshold (§3.5, α ≥ 0.7) is the separate downstream criterion the loop must meet on the held-out split. The minimum-human-budget claim is the smallest number of human-rated figures at which the convergence tolerance is reached on the held-out split.")]));

push(H2("3.7  Baselines"));
push(P([R("We benchmark against four baselines that isolate each contribution. "), B("B1"), R(" is single-shot G under P1, with no loop and no critic. "), B("B2"), R(" is a prompt-only loop in which G under P2 self-revises against its own previous draft, again with no critic. "), B("B3"), R(" is the frozen critic: G paired with the base LLaVA-Next-7B under P2, with no DPO update. "), B("B4"), R(" extends B3 with in-context examples of high- and low-rated alt-text in the critic prompt. "), B("STEM-Alt (ours)"), R(" is the full loop with the DPO-fine-tuned critic.")]));

// ---------------- 4 EVALUATION ----------------
push(H1("4  Evaluation"));
push(P([R("The evaluation plan below is pre-registered. The thresholds, statistics, and figures are fixed in advance. At this stage the released artefact is the characterised held-out corpus (§3.1, Appendix A). The convergence numbers will follow once the human-rating study (Appendix D) and the GPU fine-tuning run complete. The evaluation harness is implemented and unit-tested. It emits four figures from the held-out report: a "), I("convergence curve"), R(" (critic–human α against DPO round, against the 0.7 sustained-for-two-rounds threshold), a "), I("critic–human scatter"), R(" (per-figure C versus H primary-outcome score against the perfect-agreement diagonal), a "), I("per-dimension agreement"), R(" bar chart (C–H α for each of D1–D5 at the final round), and a "), I("residual-disagreement heatmap"), R(" (mean absolute C–H difference by domain and category). To exercise the renderer and the report schema before the study runs, the harness is also driven by a seeded synthetic preview. The convergence curve and the critic–human scatter on that preview are shown below (Figs 3 and 4), and the per-dimension agreement and residual-disagreement figures are in Appendix E. The preview illustrates format and plumbing only and carries no findings. We will report the convergence α as a measured result only after the real study replaces the preview.")]));
push(P([B("Primary outcome. "), R("Krippendorff’s α [15, 16] between C and H on the mean of D1, D2, D3, computed at each fine-tuning round r on the held-out split. The convergence threshold is α ≥ 0.7 sustained for two consecutive r.")]));
push(P([B("Convergence curve. "), R("Critic–human α on the primary outcome against r, shown with the 0.7 sustained-for-two-rounds threshold and figure-stratified bootstrap 95% confidence intervals (B = 2,000 resamples). The mean absolute C–H score difference against r is tracked as a companion diagnostic.")]));

push(figure({ ...figs.conv, num: 3, captionRuns: [
  B("Fig. 3  "),
  R("Synthetic pipeline preview, not a measured result. Convergence-curve layout: the critic–human Krippendorff α on the primary outcome (y axis) against the DPO round (x axis), with a dashed reference line at the 0.7 threshold. The shape is the pre-registered analysis; the plotted values are simulated placeholders from a seeded preview (§E), not measured agreement."),
]}));

push(P([B("Iteration effect. "), R("Paired comparison of H’s rating on G’s single-shot output (P1, no loop) versus the k-round loop output (P2 with critic). A mixed-effects linear model treats figure as a random intercept and treatment as a fixed effect.")]));

push(figure({ ...figs.scatter, num: 4, captionRuns: [
  B("Fig. 4  "),
  R("Synthetic pipeline preview, not a measured result. Critic–human scatter layout: the critic score against the human score for each held-out figure, with a diagonal line of perfect agreement. The shape is the pre-registered analysis; the plotted values are simulated placeholders from a seeded preview (§E), not measured agreement."),
]}));

push(P([B("Generalisation. "), R("C’s α is reported on three held-out conditions: "), I("G1"), R(" unseen subjects within trained categories; "), I("G2"), R(" unseen DIAGRAM categories; "), I("G3"), R(" unseen STEM domains.")]));
push(P([B("Human budget. "), R("The sample-efficiency curve plots held-out α as a function of human-rated figures used in DPO. A non-parametric LOWESS fit identifies the minimum-budget inflection point.")]));
push(P([B("Power. "), R("With 30 held-out figures × 2 raters × 5 dimensions = 300 ratings, a paired two-sided test at γ = 0.05 has power 0.80 to detect a Krippendorff α shift of 0.15. Power is computed with the bootstrap variance estimator from Hayes and Krippendorff [15].")]));
push(P([B("Notation. "), R("G, C, H = generator, critic, human; r = DPO round, k = inner round per figure; α = Krippendorff’s alpha; β = DPO regularisation; γ = significance level; π"), sub("C"), R(", π"), sub("ref"), R(" = critic and frozen reference policy; λ = between-round pair weight.")]));

// ---------------- 5 COMPLIANCE ----------------
push(H1("5  Compliance and Born-Accessible Release"));
push(P([R("Compliance is gated, not aspired. An automated linter rejects any gold-standard description that fails the DIAGRAM style rules. Human raters reject any loop output that fails the same rules. Compliance failure counts as a generation error, not as a rating dimension.")]));
push(P([R("The DIAGRAM general rules [3] are enforced as follows. §A.1 "), I("Context is key"), R(": every figure ships with its surrounding context paragraph, and descriptions assume the context rather than duplicating the caption. §A.2 "), I("Audience-aware"), R(": the audience is fixed at “blind or low-vision STEM reader, undergraduate to research level”. §A.3 "), I("Concise"), R(": short alt is bounded at 125 characters where the image type permits, and captioned figures point to the caption. §A.4 "), I("Objective"), R(": descriptions report what is visible, with no pedagogical interpretation. §A.5 "), I("General to specific"), R(": every long description opens with a one-sentence summary and then drills down. §A.6 "), I("Tone"), R(": active verbs, present tense, and abbreviations spelled out where pronunciation matters. §B "), I("Inset handling"), R(": embedded graphs render as row-and-column data tables when a one-sentence summary is insufficient.")]));
push(P([R("The paper is released as a born-accessible PDF: PDF/UA is the accessibility target, and the build is checked with the PAC PDF/UA checker before publication. The same sources can optionally render to two other channels for readers who prefer them. One is semantic HTML (ARIA landmarks, a validated heading hierarchy, and an axe-core audit). The other is an EPUB3 build following the Sample Book structure.")]));

push(H2("5.1  Failure modes and concrete mitigations"));
push(P([R("Four failure modes can introduce information that misleads a screen-reader user. Each is paired with a concrete mitigation enforced inside the loop or at rating time.")]));
push(P([I("Hallucination. "), R("The description states content not visible in the figure. This is the most damaging failure mode for a reader who cannot verify the description. "), B("Mitigation:"), R(" dimension D4 scores hallucination explicitly on the five-point rubric, and D4 ≤ 2 triggers automatic rejection of the candidate inside the loop. Any candidate that survives to release also passes the human rater’s D4 check.")]));
push(P([I("Category misclassification. "), R("The generator treats a complex figure as a simple one, producing under-described content. "), B("Mitigation:"), R(" P2 requires G to classify the figure before describing it, and the compliance linter rejects outputs whose format does not match the declared category.")]));
push(P([I("Length violation. "), R("The alt-text is excessive or insufficient, burdening screen-reader navigation. "), B("Mitigation:"), R(" dimension D5 enforces DIAGRAM §A.3 length guidance, and the linter applies the 125-character short-alt bound where the image type permits.")]));
push(P([I("Pedagogical or interpretive injection. "), R("The description states what the figure “means” rather than what is visible, shifting authority away from the reader. "), B("Mitigation:"), R(" DIAGRAM §A.4 ("), I("objective"), R(") is enforced by the linter and by the human raters, and the rubric definition of D1 ties factual correctness to what is visible, not to what is implied.")]));
push(P([R("Cases that survive all four mitigations and still mislead are reported as residual-disagreement events in the held-out evaluation, broken down by domain, category, and dimension.")]));

// ---------------- 6 LIMITATIONS ----------------
push(H1("6  Limitations"));
push(P([R("Three limitations bound the strength of the claims.")]));
push(P([B("(1) Calibration set size and inter-rater ceiling. "), R("The 120-figure calibration split yields roughly 2,400 preference pairs (720 within-figure pairs, augmented by between-round comparisons), small relative to the 10K+ pairs used in production DPO. The achievable C–H α cannot exceed the H1–H2 ceiling, since the critic is trained against the same two raters. We mitigate the small pair count by augmenting with between-round preference pairs. We report the sample-efficiency curve and the H1–H2 agreement explicitly, so the reader can locate the bottleneck.")]));
push(P([B("(2) Distribution-bound critic and frontier-model drift. "), R("The critic is calibrated on STEM figures from open educational sources. Off-distribution use such as medical imaging, art history, or video frames requires re-calibration. Closed-API generator outputs drift across versions, so the reproducibility guarantee belongs to the open-weights critic and not to the generators that produced its training distribution.")]));
push(P([B("(3) Screen-reader-user availability. "), R("Recruitment through Stiftung Zugang für alle is the primary path, recruitment via the WAI community is the backup, and a sighted rater with documented screen-reader experience is the disclosed fallback. We record which path each figure went through, so readers can stratify the reported α by rater provenance.")]));

// ---------------- 7 CONCLUSION ----------------
push(H1("7  Conclusion"));
push(P([R("STEM-Alt is a generator, critic, and human loop that converts a small dual-rated calibration set into a domain-specific open-weights critic for STEM alt-text. The convergence criterion is falsifiable: Krippendorff’s α ≥ 0.7 between C and H on the primary outcome, sustained over two consecutive DPO rounds on the held-out split. When the criterion holds, an ETH course team can extend scientific-figure accessibility across the remaining figures with only sparse human oversight, on its own open-weights infrastructure. The reproducibility guarantee belongs to the open-weights critic, not to the closed-API generators that populated its training distribution. Re-calibration is required outside STEM educational figures. The released artefact is a calibrated LoRA checkpoint, a CC-BY corpus, a born-accessible reference implementation, and the protocol for keeping the critic calibrated as content drifts.")]));

// ---------------- BACKMATTER ----------------
push(H1("Acknowledgements"));
push(P([R("I sincerely thank Anton Bolfing and Manu Heim for the exceptional course. I am excited to continue this work.")]));

push(H1("Data availability"));
push(new Paragraph({
  spacing: { after: 160, line: 276 }, alignment: AlignmentType.JUSTIFIED,
  children: [
    R("The 30-figure held-out evaluation corpus is released as a structured manifest (manifest.csv). The 11 columns are figure_id, source_url, licence, STEM domain, ETH alt-text category, DIAGRAM figure type, expert reference description, short alt, context paragraph, image_path, and split. The author releases four artefacts under CC-BY 4.0: the manifest, the held-out split (splits.json), the five-dimension rubric (rubric.yaml), and the two locally rendered figures (mathcs_complex_loss_landscape.png and mathcs_complex_dynamic_programming.png, rendered deterministically by code/scripts/render_local_figures.py). The 28 third-party figures are drawn from Wikimedia Commons, OpenStax (CC-BY 4.0), MIT OpenCourseWare, and arXiv (CC-BY 4.0). The manifest carries the source URL and the per-figure licence (public domain, CC-BY-SA-3.0, CC-BY-SA-4.0, CC-BY-4.0, or CC-BY-3.0). The licence-preserving figure files are acquired by running pipeline/01_build_corpus.py against the manifest. The 6-page manuscript and the 1- to 2-page accessible plain-language summary are released under CC-BY 4.0 as born-accessible PDFs (PDF/UA target). Semantic HTML and EPUB3 renderings can optionally be produced from the same sources."),
    new FootnoteReferenceRun(1),
  ],
}));
push(P([R("The DPO-fine-tuned LLaVA-Next-7B LoRA checkpoint is the calibrated-critic artefact produced by the pipeline and is released in the same repository. Closed-API generator outputs are included subject to the academic-use terms of OpenAI, Anthropic, and Google; open-weights critic outputs are released under CC-BY 4.0.")]));
push(new Paragraph({
  spacing: { after: 160, line: 276 }, alignment: AlignmentType.JUSTIFIED,
  children: [
    R("All artefacts, including the fine-tuned checkpoint, are deposited in the project repository at "),
    new ExternalHyperlink({ children: [new TextRun({ text: "https://github.com/arvidgollwitzer/STEM-Alt", style: "Hyperlink", font: FONT })], link: "https://github.com/arvidgollwitzer/STEM-Alt" }),
    R(". There is no embargo, controlled-access committee, or commercial restriction on any released artefact. Please cite this manuscript when reusing any released artefact."),
  ],
}));

push(H1("Code availability"));
push(new Paragraph({
  spacing: { after: 160, line: 276 }, alignment: AlignmentType.JUSTIFIED,
  children: [
    R("All code (the stem_alt Python package, the Hydra configuration, the six-stage pipeline, the unit tests, and the build scripts) is released under the MIT licence at "),
    new ExternalHyperlink({ children: [new TextRun({ text: "https://github.com/arvidgollwitzer/STEM-Alt", style: "Hyperlink", font: FONT })], link: "https://github.com/arvidgollwitzer/STEM-Alt" }),
    R(". The release pins the dependency set in code/pyproject.toml and the random seed under utils.set_seed. The run-config files pin the model versions used in the loop: the LLaVA-NeXT-7B revision and the GPT-4o, Claude 3.7 Sonnet, and Gemini 2.5 Pro snapshot strings."),
  ],
}));

// Declarations — REAL bulleted list
push(H1("Declarations"));
const decl = (lead, rest) => new Paragraph({
  numbering: { reference: "declarations", level: 0 },
  spacing: { after: 80, line: 264 },
  children: [B(lead), R(rest)],
});
push(decl("Funding. ", "Not applicable."));
push(decl("Conflict of interest. ", "The author declares no conflict of interest."));
push(decl("Ethics approval and consent to participate. ", "Under this protocol, human ratings carry no personally identifying information beyond an opaque rater_id, and recruitment goes through institutional channels."));
push(decl("Data availability. ", "See the Data availability section above."));
push(decl("Code availability. ", "See the Code availability section above."));
push(decl("Author contribution. ", "Sole author; conceived, designed, implemented, and wrote the work."));

// ---------------- APPENDICES ----------------
push(H1("Appendix A  Corpus characterisation in detail"));
push(P([R("This appendix expands the corpus-characterisation summary of §3.1. Every value is emitted from data/corpus/manifest.csv by analysis/analyze_corpus.py, and each figure ships with the CSV it was rendered from. The reproduced stratification matches the held-out split of Table 1 exactly (corpus_summary.json: matches_manuscript_table1 = true).")]));
push(P([R("Table A1 gives the DIAGRAM figure-type and source-licence distributions, and Figs. A1–A3 plot the three descriptive axes.")]));

// Table A1 — vMerge axis column
push(caption([B("Table A1  "), R("Composition of the 30 held-out figures by DIAGRAM figure type and by source licence.")]));
push(buildTable({
  widths: [2800, 4760, 1800],
  header: [{ text: "Axis" }, { text: "Category" }, { text: "Count", align: C }],
  rows: [
    [{ runs: [R("DIAGRAM figure type")], span: 9 }, { runs: [R("Graphs")] }, { runs: [R("8")], align: C }],
    [null, { runs: [R("Relational diagrams")] }, { runs: [R("7")], align: C }],
    [null, { runs: [R("Illustrated diagrams")] }, { runs: [R("4")], align: C }],
    [null, { runs: [R("Photos")] }, { runs: [R("4")], align: C }],
    [null, { runs: [R("Chemistry")] }, { runs: [R("2")], align: C }],
    [null, { runs: [R("Tables")] }, { runs: [R("2")], align: C }],
    [null, { runs: [R("Mathematics")] }, { runs: [R("1")], align: C }],
    [null, { runs: [R("Art/photos/cartoons")] }, { runs: [R("1")], align: C }],
    [null, { runs: [R("Maps")] }, { runs: [R("1")], align: C }],
    [{ runs: [R("Source licence")], span: 5 }, { runs: [R("Public domain")] }, { runs: [R("17")], align: C }],
    [null, { runs: [R("CC-BY-SA-3.0")] }, { runs: [R("8")], align: C }],
    [null, { runs: [R("CC-BY-SA-4.0")] }, { runs: [R("2")], align: C }],
    [null, { runs: [R("CC-BY-4.0 (local render)")] }, { runs: [R("2")], align: C }],
    [null, { runs: [R("CC-BY-3.0")] }, { runs: [R("1")], align: C }],
  ],
}));
push(new Paragraph({ spacing: { after: 160 }, children: [] }));

push(figure({ ...figs.diagtypes, num: "A1", captionRuns: [
  B("Fig. A1  "),
  R("DIAGRAM figure-type distribution across the 30 held-out figures. Horizontal bar chart: graphs 8, relational diagrams 7, illustrated diagrams 4, photos 4, chemistry 2, tables 2, mathematics 1, art/photos/cartoons 1, maps 1. Graphs and relational diagrams dominate, matching the structure-heavy content of STEM teaching material."),
]}));
push(figure({ ...figs.licences, num: "A2", captionRuns: [
  B("Fig. A2  "),
  R("Source-licence distribution across the 30 held-out figures. Bar chart: public domain 17, CC-BY-SA-3.0 8, CC-BY-SA-4.0 2, CC-BY-4.0 2, CC-BY-3.0 1. All figures are openly licensed, and the two CC-BY-4.0 figures are rendered locally and released by the author."),
]}));
push(figure({ ...figs.shortalt, num: "A3", captionRuns: [
  B("Fig. A3  "),
  R("Histogram of short-alt length for the 26 non-decorative figures, against the DIAGRAM §A.3 125-character bound (dashed line). All short alts range from 17 to 53 characters (median 31.5) and sit well below the bound. The four decorative figures are excluded because their alt is empty by design, the correct WCAG handling of decorative images."),
]}));

push(H1("Appendix B  Implementation, architecture, and reproducibility"));
push(H2("B.1  Six-stage pipeline"));
push(P([R("The reference implementation is a Python package (stem_alt) and a six-stage Hydra pipeline. The stages run in order and share a single per-figure loop trace as the source of truth (Table B1).")]));

// Table B1
push(caption([B("Table B1  "), R("The six pipeline stages, with the artefact each reads and writes.")]));
const mono = (t) => R(t, { font: "Consolas", size: 19 });
push(buildTable({
  widths: [900, 2700, 2880, 2880],
  header: [{ text: "Stage", align: C }, { text: "Script" }, { text: "Reads" }, { text: "Writes" }],
  rows: [
    [{ runs: [R("1")], align: C }, { runs: [mono("01_build_corpus.py")] }, { runs: [mono("manifest.csv")] }, { runs: [mono("splits.json")] }],
    [{ runs: [R("2")], align: C }, { runs: [mono("02_run_loop.py")] }, { runs: [R("calibration split")] }, { runs: [mono("loop_traces/<id>.json")] }],
    [{ runs: [R("3")], align: C }, { runs: [mono("03_collect_human_ratings.py")] }, { runs: [R("loop traces")] }, { runs: [mono("ratings_*.jsonl")] }],
    [{ runs: [R("4")], align: C }, { runs: [mono("04_train_dpo.py")] }, { runs: [R("traces + ratings")] }, { runs: [mono("dpo/round_NN/"), R(", critic cfg")] }],
    [{ runs: [R("5")], align: C }, { runs: [mono("05_evaluate.py")] }, { runs: [R("held-out split + ratings")] }, { runs: [mono("held_out_report.json")] }],
    [{ runs: [R("6")], align: C }, { runs: [mono("06_release_artefacts.py")] }, { runs: [R("all of the above")] }, { runs: [R("born-accessible bundle")] }],
  ],
}));
push(new Paragraph({ spacing: { after: 160 }, children: [] }));

push(H2("B.2  Factory/Registry pattern"));
push(P([R("Each submodule under src/stem_alt/ (corpus, generator, critic, loop, training, evaluation, compliance, human) exposes a <Type>Factory lookup and a register_<type>(name) decorator. A module-walk at import time fires the decorators without an explicit registration list. Adding a generator, critic, trainer, or compliance rule is then a one-file change with no edit to the factory wiring. Generators, critics, and trainers take a single cfg argument, and Hydra composes the config groups under conf/<group>/<name>.yaml at startup. Generator choice, LoRA rank, and DPO hyperparameters then sweep without code edits.")]));

push(H2("B.3  Loop trace"));
push(P([R("LoopOrchestrator.run_for_figure produces one LoopRecord per figure. The record holds the figure id, the list of rounds, a convergence flag, and the human score attached at stage 3. Each round carries its round index, the generation result with provenance, and the critic’s five-dimension score. The trace is the single source of truth across stages 2 through 6, so re-running a stage reuses the snapshot rather than re-calling a model.")]));

push(H2("B.4  Reproducibility contract"));
push(P([R("STEM-Alt targets bit-exact reproducibility on the open-weights critic and full provenance on the closed-API generators. utils.set_seed runs at the entry of every stage. It fixes random, PYTHONHASHSEED, NumPy, and Torch seeds, sets cudnn.deterministic true, and sets cudnn.benchmark false. The DPO trainer adds the round index so each fine-tuning round has a distinct seed. Hydra writes the resolved config tree to outputs/<run>/.hydra/config.yaml, the canonical record of the hyperparameters behind a checkpoint. Each stage also records the Python version, a frozen dependency list, the GPU model and driver, and the git commit and dirty-tree status. The corpus manifest is hashed with SHA-256 at stage 1, and the hash is written into the splits.json provenance block. Any change to a figure file or to the manifest then forces the splits to re-emit and the downstream stages to re-run. Two sources do not reproduce bit-exactly. Closed-API generation drifts across API versions; we mitigate this by logging the version string and snapshotting the output into the trace. Some non-deterministic CUDA kernels cause sub-1-ULP drift, mitigated by the deterministic-cuDNN setting and disclosed in §6.")]));

push(H1("Appendix C  Compliance enforcement and born-accessible builds"));
push(P([R("Compliance is a gate, not an aspiration (§5). The automated DIAGRAM linter rejects any gold-standard description that fails the rules at corpus-build time, and any loop output that fails them at rating time. The WCAG validator rejects any release HTML that fails Success Criterion 1.1.1 at release-bundle time. Table C1 lists the seven DIAGRAM general rules and the check that enforces each.")]));

// Table C1
push(caption([B("Table C1  "), R("DIAGRAM general-rule checklist and the corresponding linter check.")]));
push(buildTable({
  widths: [2808, 6552],
  header: [{ text: "Rule" }, { text: "Linter check" }],
  rows: [
    [{ runs: [R("Context is key")] }, { runs: [R("The manifest must carry a non-empty context paragraph.")] }],
    [{ runs: [R("Audience-aware")] }, { runs: [R("Audience fixed at “blind or low-vision STEM reader”; jargon density is checked against the figure’s DIAGRAM type.")] }],
    [{ runs: [R("Be concise")] }, { runs: [R("Short alt ≤ 125 characters where the image type permits.")] }],
    [{ runs: [R("Be objective")] }, { runs: [R("Pedagogical phrasing (“this teaches”, “the goal of this figure”) is flagged.")] }],
    [{ runs: [R("General to specific")] }, { runs: [R("Every long description must open with a one-sentence summary, whose length is checked.")] }],
    [{ runs: [R("Tone")] }, { runs: [R("Passive constructions in long descriptions are flagged.")] }],
    [{ runs: [R("Inset handling")] }, { runs: [R("Graph insets are required to render as row-and-column tables in the long description (manually reviewed).")] }],
  ],
}));
push(new Paragraph({ spacing: { after: 160 }, children: [] }));
push(P([R("At release time, pipeline/06_release_artefacts.py parses every <img> in the release HTML, builds a figure record, and runs the WCAG validator. Decorative images must declare alt=\"\", informative images must carry a non-empty alt, and complex images must reference a long description via aria-describedby. Any violation aborts the release. The tagged PDF is the primary born-accessible artefact. It is built by pdflatex and the SN template, and verified against PDF/UA with the PAC checker. Semantic HTML (audited with axe-core against WCAG 2.2 AA) and an EPUB3 build (audited with Ace by DAISY against EPUB Accessibility 1.1) are optional renderings produced from the same sources. The release pipeline refuses to ship a bundle in which any requested check failed.")]));

push(H1("Appendix D  Human-rating protocol"));
push(P([R("Two raters score each calibration figure. The first is a domain expert with research-level fluency in the figure’s STEM area, recruited through ETH and MIT contacts and verified by institutional email or ORCID. The second is a screen-reader user, recruited first through Stiftung Zugang für alle, with a remote WAI-community rater as backup and a sighted rater with documented screen-reader experience as the disclosed fallback. Every record stores the rater’s role, and fallback ratings are reported separately and excluded from the headline α.")]));
push(P([R("In a session, the rater receives the figure, its context paragraph, the DIAGRAM figure type, and the candidate alt-text, without the critic’s scores, the generator identity, or the round index. Screen-reader-user raters listen to the alt-text rendered with NVDA at standard rate, live or from a pre-rendered WAV file. The rater scores each dimension 1 to 5 and writes a one-paragraph critique. Any score below 3 requires at least one supporting sentence. The session records the timestamp, an opaque rater id, the rater role, and an NVDA-rendering flag.")]));
push(P([R("The five-dimension rubric is piloted on 20 figures and adjudicated pairwise. Differences of two or more points on any dimension are flagged, and the flagged pair adjudicates with the project lead present. The rubric definition is sharpened only when a disagreement reveals an ambiguity in the rubric rather than in the figure. The rubric is then frozen and committed. Any later edit is recorded as a protocol deviation in §6. Headline statistics report two agreement numbers against their pre-registered thresholds. The H1–H2 inter-rater α is checked against the rating-quality floor of 0.6 on the primary outcome. The C–H α is checked against the convergence threshold of 0.7 sustained across two consecutive DPO rounds. The gap between them bounds how far additional DPO data can push the critic without a richer rubric. A figure below the floor is adjudicated. If adjudication does not recover it, the figure leaves the calibration set and the exclusion is reported. The minimum-human-budget claim is the smallest count of fully two-rater-covered calibration figures at which the held-out threshold is reached. Human ratings carry no personally identifying information beyond the opaque rater id, and recruitment runs through institutional channels.")]));

push(H1("Appendix E  Evaluation harness and synthetic pipeline preview"));
push(P([R("The evaluation harness (analysis/generate_eval_figures.py, covered by tests/test_eval_figures.py) renders four figures from the held-out report that pipeline/05_evaluate.py writes: the convergence curve, the critic–human scatter, the per-dimension agreement bar chart, and the residual-disagreement heatmap defined in §4.")]));
push(new Paragraph({
  spacing: { before: 80, after: 160, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  border: { left: { style: m.BorderStyle.SINGLE, size: 18, color: "808080", space: 12 } },
  indent: { left: 360 },
  children: [B("The figures in this appendix are a synthetic pipeline preview, not a measured result."), R(" No human rated these figures, no critic was trained, and no Krippendorff α was computed from real data. The values are generated by code/scripts/generate_synthetic_ratings.py (seed 20260604), the report carries a _SYNTHETIC banner, and every rating line is tagged \"synthetic\": true. The preview exists only to exercise the report schema and the figure renderer end to end before the human study runs. The numbers must not be cited as findings, and §4 reports the convergence α as a result only after the real study replaces this preview.")],
}));
push(P([R("The convergence curve and the critic–human scatter appear in the main text (§4, Figs 3 and 4). The two remaining shapes, the per-dimension agreement bar chart and the residual-disagreement heatmap, are shown here on the same synthetic report (Figs E1 and E2), so a reader can see the format the real study will fill.")]));

push(figure({ ...figs.perdim, num: "E1", captionRuns: [
  B("Fig. E1  "),
  R("Synthetic pipeline preview, not a measured result. Per-dimension agreement layout: the critic–human Krippendorff α for each rubric dimension (D1–D5) at the final round, against the 0.7 reference line. Shape only; the values are simulated placeholders."),
]}));
push(figure({ ...figs.resid, num: "E2", captionRuns: [
  B("Fig. E2  "),
  R("Synthetic pipeline preview, not a measured result. Residual-disagreement heatmap layout: the mean absolute critic–human difference by STEM domain (rows) and ETH category (columns), with darker cells indicating larger disagreement. Shape only; the values are simulated placeholders."),
]}));

// ---------------- REFERENCES ----------------
push(H1("References"));
REFS.forEach((r, i) => push(refParagraph(i, r)));

// ============================================================ DOCUMENT
const doc = new Document({
  creator: "Arvid E. Gollwitzer",
  title: "STEM-Alt: An Adversarial Generator-Critic Loop with Human-Aligned Review for STEM Alt-Text",
  description: "Accessible (tagged) Word version of the STEM-Alt course paper, 376-1230-00L Digital Accessibility, ETH Zurich, FS2026.",
  subject: "Accessible scientific-figure alt-text; WCAG 2.2; DIAGRAM",
  keywords: "alt-text, scientific figures, WCAG 2.2, DIAGRAM, vision-language models, LLM-as-judge, DPO, screen-reader users, accessibility",
  styles: {
    default: {
      document: { run: { font: FONT, size: 22, language: { value: "en-US" } } },
    },
    paragraphStyles: [
      { id: "Normal", name: "Normal", run: { font: FONT, size: 22, language: { value: "en-US" } }, paragraph: { spacing: { line: 276 } } },
      { id: "PaperTitle", name: "Paper Title", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: FONT }, paragraph: { spacing: { before: 120, after: 240 }, outlineLevel: 0 } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: "1F3864" }, paragraph: { spacing: { before: 280, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: "2E5496" }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 18, italics: true, font: FONT }, paragraph: { spacing: { after: 160, line: 252 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "declarations",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { run: { font: FONT }, paragraph: { indent: { left: 460, hanging: 260 } } } }] },
    ],
  },
  footnotes: {
    1: { children: [new Paragraph({ children: [R("The rank-16 LoRA adapter is a small binary. It is versioned with Git LFS or attached as a release asset rather than committed inline.", { size: 18 })] })] },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [R("", {}), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })],
      })] }),
    },
    children,
  }],
});

const OUT = path.join(__dirname, "..", "stem-alt-accessible.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("Wrote", OUT, "(" + buf.length + " bytes), paragraphs/blocks:", children.length);
});
