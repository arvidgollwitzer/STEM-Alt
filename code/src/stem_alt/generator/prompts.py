"""Prompt templates P1 (generic) and P2 (WCAG-aware).

P2 names the four ETH alt-text categories and embeds the DIAGRAM general
rules. A one-shot example from the DIAGRAM Sample Book is injected at
runtime by the orchestrator so the example pool can be rotated.
"""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

P1_GENERIC = "Provide alt-text for this image suitable for a blind reader."


P2_WCAG_AWARE = dedent(
    """
    You are drafting alt-text for a STEM figure to be read aloud by a screen
    reader. The reader is a blind or low-vision STEM student or researcher.

    Step 1. Classify the figure into exactly one of the four ETH alt-text
    categories:
      - simple:      a one-off decorative or contextual image (use a short alt)
      - linked:      the image is clickable and goes somewhere meaningful
                     (alt names the destination)
      - decorative:  pure visual decoration with no informational content
                     (use an empty alt attribute, alt="")
      - complex:     the image carries information the surrounding text does
                     not (use a short alt PLUS a long description)

    Step 2. Apply the DIAGRAM general rules:
      1. Context is key: assume the surrounding paragraph below; do not
         duplicate the caption.
      2. Be concise: short alt at most 125 characters when the image type
         permits.
      3. Be objective: report what is visible. No author intent, no
         pedagogical interpretation.
      4. General to specific: every long description opens with a one-sentence
         summary, then drills down.
      5. Active verbs, present tense. Spell out abbreviations where
         pronunciation matters.

    Surrounding paragraph (from the source):
    ---
    {context}
    ---

    Output strictly the following block:
      CATEGORY: <one of simple|linked|decorative|complex>
      SHORT_ALT: <text or empty>
      LONG_DESCRIPTION: <text, empty if not complex>
    """
).strip()


REVISION_SUFFIX = dedent(
    """
    The critic raised the following concerns on your previous draft.
    Address every concern and re-emit the full block.

    Critic critique:
    ---
    {previous_critique}
    ---
    """
).strip()


def assemble_prompt(
    prompt_name: str,
    context: str,
    previous_critique: Optional[str],
) -> str:
    """Compose the user-side prompt for a single generation call."""
    if prompt_name == "P1":
        base = P1_GENERIC
    elif prompt_name == "P2":
        base = P2_WCAG_AWARE.format(context=context)
    else:
        raise ValueError(f"Unknown prompt name: {prompt_name}")
    if previous_critique:
        return base + "\n\n" + REVISION_SUFFIX.format(previous_critique=previous_critique)
    return base
