// Generate an accessible (tagged) Word document from the STEM-Alt paper.pdf content.
// Content is reproduced from ../stem-alt.tex / ../stem-alt.pdf verbatim.
// Accessibility: real Heading styles (outline levels), alt text on every image,
// real tables with marked header rows + captions, a real bulleted list, a real
// footnote, a numbered reference list, document language en-US, and core metadata.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, Header, Footer,
  ExternalHyperlink, FootnoteReferenceRun, TabStopType, TabStopPosition,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");           // project work/
const FIGDIR_M = path.join(ROOT, "manuscript", "figures");
const FIGDIR_D = path.join(ROOT, "demo", "figures");

// ---------- helpers ----------
const FONT = "Arial";
function R(text, o = {}) { return new TextRun({ text, font: FONT, ...o }); }
function B(text, o = {}) { return R(text, { bold: true, ...o }); }
function I(text, o = {}) { return R(text, { italics: true, ...o }); }
function sub(text) { return R(text, { subScript: true }); }
function sup(text) { return R(text, { superScript: true }); }

function P(children, o = {}) {
  return new Paragraph({
    children: Array.isArray(children) ? children : [R(children)],
    spacing: { after: 160, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    ...o,
  });
}
function H1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [R(text)] });
}
function H2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [R(text)] });
}
function caption(runs) {
  return new Paragraph({
    style: "Caption",
    children: runs,
    spacing: { before: 80, after: 200 },
    alignment: AlignmentType.LEFT,
  });
}

// Figure: visible caption (matches PDF) + image carrying standalone alt text.
function figure({ file, num, captionRuns, alt, w, h }) {
  const data = fs.readFileSync(file);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 40 },
      children: [
        new ImageRun({
          type: "png",
          data,
          transformation: { width: w, height: h },
          altText: {
            title: `Figure ${num}`,
            name: `Figure ${num}`,
            description: alt,
          },
        }),
      ],
    }),
    caption(captionRuns),
  ];
}

// ---------- tables ----------
const HDR_FILL = "D9E2F3";
const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };

function tcell(runs, { width, header = false, fill, span, align = AlignmentType.LEFT, valign = VerticalAlign.CENTER } = {}) {
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    rowSpan: span,
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    verticalAlign: valign,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    children: [new Paragraph({ alignment: align, spacing: { after: 0 }, children: runs })],
  });
}

// Generic table builder. `header` row gets tableHeader=true + shading.
function buildTable({ widths, header, rows }) {
  const total = widths.reduce((a, b) => a + b, 0);
  const trs = [];
  trs.push(new TableRow({
    tableHeader: true,
    children: header.map((h, i) =>
      tcell([B(h.text)], { width: widths[i], header: true, fill: HDR_FILL, align: h.align || AlignmentType.LEFT })),
  }));
  for (const row of rows) {
    trs.push(new TableRow({
      children: row.map((c, i) => {
        if (c === null) return null; // covered by a rowSpan above
        return tcell(c.runs, { width: widths[c.col ?? i], span: c.span, align: c.align || AlignmentType.LEFT, fill: c.fill });
      }).filter(Boolean),
    }));
  }
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: trs,
  });
}

// ============================================================ FIGURES
// Alt text is read VERBATIM from the ALT_TEXT.md shipped in each figure
// directory (the single source of truth), so it never drifts from the repo.
function parseAltText(mdPath) {
  const txt = fs.readFileSync(mdPath, "utf8");
  const map = {};
  for (const part of txt.split(/^##\s+/m).slice(1)) {
    const nl = part.indexOf("\n");
    const name = part.slice(0, nl).trim();
    let body = part.slice(nl + 1).trim();
    body = body.replace(/`/g, "").replace(/\s+/g, " ").trim(); // drop markdown backticks, normalise whitespace
    map[name] = body;
  }
  return map;
}
const ALT_M = parseAltText(path.join(FIGDIR_M, "ALT_TEXT.md"));
const ALT_D = parseAltText(path.join(FIGDIR_D, "ALT_TEXT.md"));
function altOf(map, key) {
  const v = map[key];
  if (!v) throw new Error(`No ALT_TEXT entry for ${key}`);
  return v;
}

// Each figure maps to the file used in the document and that file's own
// ALT_TEXT.md entry (verbatim).
const figs = {
  overview:  { file: path.join(FIGDIR_M, "fig_overview.png"),                  w: 600, h: 335, alt: altOf(ALT_M, "fig_overview.png") },
  strat:     { file: path.join(FIGDIR_M, "fig_corpus_stratification_pub.png"), w: 470, h: 352, alt: altOf(ALT_M, "fig_corpus_stratification_pub.png") },
  conv:      { file: path.join(FIGDIR_D, "fig_convergence_curve.png"),         w: 520, h: 321, alt: altOf(ALT_D, "fig_convergence_curve.png") },
  scatter:   { file: path.join(FIGDIR_D, "fig_ch_scatter.png"),                w: 430, h: 432, alt: altOf(ALT_D, "fig_ch_scatter.png") },
  diagtypes: { file: path.join(FIGDIR_M, "fig2_diagram_types.png"),            w: 540, h: 320, alt: altOf(ALT_M, "fig2_diagram_types.png") },
  licences:  { file: path.join(FIGDIR_M, "fig3_licences.png"),                 w: 540, h: 320, alt: altOf(ALT_M, "fig3_licences.png") },
  shortalt:  { file: path.join(FIGDIR_M, "fig4_short_alt_length.png"),         w: 540, h: 320, alt: altOf(ALT_M, "fig4_short_alt_length.png") },
  perdim:    { file: path.join(FIGDIR_D, "fig_per_dimension.png"),             w: 500, h: 329, alt: altOf(ALT_D, "fig_per_dimension.png") },
  resid:     { file: path.join(FIGDIR_D, "fig_residual_heatmap.png"),          w: 500, h: 352, alt: altOf(ALT_D, "fig_residual_heatmap.png") },
};

// ============================================================ REFERENCES
const REFS = [
  [ "W3C Web Accessibility Initiative: Understanding Success Criterion 1.1.1: Non-text Content. WCAG 2.2 Understanding Docs (2025).", "https://www.w3.org/WAI/WCAG22/Understanding/non-text-content" ],
  [ "Bolfing, A., Heim, M.: AI Opportunities for Accessibility and Inclusion; Accessibility in Higher Education. Lecture 12, 376-1230-00L Digital Accessibility, FS2026, ETH Zürich, D-HEST. Slide deck on Moodle, lecture delivered 7 May 2026 (2026).", null ],
  [ "DIAGRAM Center, National Center for Accessible Media: Image Description Guidelines (2019).", "http://diagramcenter.org/table-of-contents-2.html" ],
  [ "DIAGRAM Center: Accessible Image Sample Book (2019).", "http://diagramcenter.org/standards-and-practices/accessible-image-sample-book.html" ],
  [ "ETH Zurich: Image Descriptions — Alternative Texts. ETH Staffnet, Accessibility and Inclusion in Teaching (2026).", "https://ethz.ch/staffnet/en/teaching/accessibility-and-inclusion-in-teaching/accessibility-concepts/text-alternatives.html" ],
  [ "ETH Zurich: Text Alternatives: Complex Illustrations — Examples. ETH Staffnet (2026).", "https://ethz.ch/staffnet/en/teaching/accessibility-and-inclusion-in-teaching/accessibility-concepts/text-alternatives/complex-illustrations-examples.html" ],
  [ "Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E.P., Zhang, H., Gonzalez, J.E., Stoica, I.: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. In: Advances in Neural Information Processing Systems (Datasets and Benchmarks Track) (2023).", "https://arxiv.org/abs/2306.05685" ],
  [ "Liu, Y., Iter, D., Xu, Y., Wang, S., Xu, R., Zhu, C.: G-Eval: NLG evaluation using GPT-4 with better human alignment. In: Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (2023).", "https://doi.org/10.18653/v1/2023.emnlp-main.153" ],
  [ "Zhu, L., Wang, X., Wang, X.: JudgeLM: Fine-tuned large language models are scalable judges. In: International Conference on Learning Representations (2025). ICLR 2025 Spotlight.", "https://openreview.net/forum?id=xsELpEPn4A" ],
  [ "Kim, S., Shin, J., Cho, Y., Jang, J., Longpre, S., Lee, H., Yun, S., Shin, S., Kim, S., Thorne, J., Seo, M.: Prometheus: Inducing fine-grained evaluation capability in language models. In: International Conference on Learning Representations (2024).", "https://arxiv.org/abs/2310.08491" ],
  [ "Liu, H., Li, C., Li, Y., Li, B., Zhang, Y., Shen, S., Lee, Y.J.: LLaVA-NeXT: Improved Reasoning, OCR, and World Knowledge. Blog post, 30 January 2024 (2024).", "https://llava-vl.github.io/blog/2024-01-30-llava-next/" ],
  [ "Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C.D., Finn, C.: Direct preference optimization: Your language model is secretly a reward model. In: Advances in Neural Information Processing Systems (2023).", "https://arxiv.org/abs/2305.18290" ],
  [ "Christiano, P.F., Leike, J., Brown, T.B., Martic, M., Legg, S., Amodei, D.: Deep reinforcement learning from human preferences. In: Advances in Neural Information Processing Systems (2017).", "https://arxiv.org/abs/1706.03741" ],
  [ "Hu, E.J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., Chen, W.: LoRA: Low-rank adaptation of large language models. In: International Conference on Learning Representations (2022).", "https://arxiv.org/abs/2106.09685" ],
  [ "Hayes, A.F., Krippendorff, K.: Answering the call for a standard reliability measure for coding data. Communication Methods and Measures 1(1), 77–89 (2007).", "https://doi.org/10.1080/19312450709336664" ],
  [ "Krippendorff, K.: Computing Krippendorff's Alpha-Reliability. Annenberg School for Communication, University of Pennsylvania (2011).", "https://www.asc.upenn.edu/sites/default/files/2021-03/Computing-Krippendorff-Alpha-Reliability.pdf" ],
];
function refParagraph(idx, [text, url]) {
  const kids = [B(`[${idx + 1}] `), R(text + (url ? " " : ""))];
  if (url) kids.push(new ExternalHyperlink({ children: [new TextRun({ text: url, style: "Hyperlink", font: FONT })], link: url }));
  return new Paragraph({ children: kids, spacing: { after: 120, line: 264 }, alignment: AlignmentType.LEFT });
}

module.exports = {
  fs, path, Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, Header, Footer, ExternalHyperlink,
  FootnoteReferenceRun, TabStopType, TabStopPosition,
  R, B, I, sub, sup, P, H1, H2, caption, figure, buildTable, tcell,
  figs, REFS, refParagraph, FONT, HDR_FILL,
};
