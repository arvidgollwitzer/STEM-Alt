#!/usr/bin/env bash
# Build the STEM-Alt manuscript using the Springer Nature article template.
#
# The LaTeX source `stem-alt.tex` is the canonical (and only) form of the
# paper; this script renders it to `stem-alt.pdf`. The plain-language
# `accessible-summary.md` is built separately to PDF by
# `code/scripts/build_pdfs.sh`.
#
# Toolchain: pdflatex + bibtex from TeX Live (TinyTeX works).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# Use the SN bst files shipped alongside the class.
export BSTINPUTS="bst::"
export TEXINPUTS="${HERE}::"

pdflatex -interaction=nonstopmode stem-alt.tex >/dev/null
bibtex stem-alt
pdflatex -interaction=nonstopmode stem-alt.tex >/dev/null
pdflatex -interaction=nonstopmode stem-alt.tex >/dev/null

# Tidy intermediate files; keep the .pdf and the .bbl (the .bbl is the
# rendered bibliography that Nature Portfolio submission systems often
# want pasted into the .tex).
rm -f stem-alt.aux stem-alt.log stem-alt.out stem-alt.blg

echo "Built: $HERE/stem-alt.pdf"
ls -lh stem-alt.pdf
