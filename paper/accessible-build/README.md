# Accessible Word build

Generates `../stem-alt-accessible.docx` — an accessible (tagged) Word version of
`../stem-alt.pdf`, reproduced from `../stem-alt.tex`.

## Rebuild
```bash
npm install docx
node doc.js   # requires build.js (helpers) in the same folder
```

## Accessibility features
- Title style + Heading 1/2 with outline levels (structure tags)
- Alt text on all 9 figures (from manuscript/figures/ALT_TEXT.md + demo/figures/ALT_TEXT.md)
- 5 real tables, each with a marked header row (w:tblHeader)
- Real bulleted list (Declarations), real footnote, numbered reference list
- Document language en-US; core properties (title/author/keywords)

Export to tagged PDF/UA from Word: File → Save As → PDF → Options →
"Document structure tags for accessibility".
