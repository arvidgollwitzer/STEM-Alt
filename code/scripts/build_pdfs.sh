#!/usr/bin/env bash
# Build accessible-summary.pdf from its markdown source in paper/.
# Drops the PDF into paper/ alongside the LaTeX paper.
#
# The main paper.pdf is built from LaTeX via ../../paper/build.sh using the
# Springer Nature article template; this script only renders the plain-language
# accessible summary.
#
# Toolchain:
#   - pandoc >= 3.0
#   - xelatex (from TeX Live or MacTeX)

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/../.." && pwd)"
PAPER="$PROJECT_ROOT/paper"

# Summary uses a single-column 11pt layout with 0.85in margins. The FPD caps
# the accessible plain-language summary at 1 to 2 pages; this layout lands
# the polished prose within that bound while staying readable on screen and
# in print.
SUMMARY_OPTS=(
  --pdf-engine=xelatex
  -V documentclass=article
  -V fontsize=11pt
  -V geometry:margin=0.85in
  -V colorlinks=true
  -V linkcolor=NavyBlue
  -V urlcolor=NavyBlue
  -V citecolor=NavyBlue
  -V mainfont="Helvetica"
  -V monofont="Menlo"
  --metadata=lang:en
  --table-of-contents=false
  --highlight-style=tango
)

echo "Building accessible-summary.pdf..."
pandoc "$PAPER/accessible-summary.md" \
  "${SUMMARY_OPTS[@]}" \
  --metadata=title:"STEM-Alt: A Plain-Language Summary" \
  --metadata=author:"Arvid E. Gollwitzer (arvidg@mit.edu)" \
  --metadata=keywords:"alt-text;accessibility;STEM;summary" \
  -o "$PAPER/accessible-summary.pdf"

echo "Done. PDF:"
ls -lh "$PAPER/accessible-summary.pdf"
echo "(the paper PDF, stem-alt.pdf, is built separately by ../../paper/build.sh)"
