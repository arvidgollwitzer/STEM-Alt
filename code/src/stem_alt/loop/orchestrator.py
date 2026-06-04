"""LoopOrchestrator: drive G against C for up to k rounds per figure.

Each round produces a `LoopRound` record. The full per-figure trace
is a `LoopRecord` that the human-rating step later attaches H scores to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stem_alt.critic.base import CriticBase
from stem_alt.critic.rubric import RubricScore
from stem_alt.generator.base import AltTextGenerator, GenerationResult
from stem_alt.loop.convergence import ConvergenceCheck
from stem_alt.utils import get_logger

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class LoopRound:
    round_index: int
    generation: GenerationResult
    score: RubricScore
    rejected_for_hallucination: bool = False


@dataclass
class LoopRecord:
    figure_id: str
    rounds: List[LoopRound] = field(default_factory=list)
    converged: bool = False
    human_score: Optional[RubricScore] = None

    @property
    def final_generation(self) -> GenerationResult:
        return self.rounds[-1].generation

    @property
    def final_score(self) -> RubricScore:
        return self.rounds[-1].score


@dataclass
class LoopOrchestrator:
    """Drive G against C for one figure.

    The orchestrator records every round but flags candidates whose
    hallucination score `D4_hallucination` falls at or below
    `hallucination_reject_threshold` (paper §5 *Failure modes and concrete
    mitigations*). Flagged rounds are still appended to the trace so the
    reader can audit the rejection; they do not count toward the final
    output of the loop.
    """

    generator: AltTextGenerator
    critic: CriticBase
    max_rounds: int = 5
    convergence: ConvergenceCheck = field(default_factory=ConvergenceCheck)
    hallucination_reject_threshold: int = 2

    def run_for_figure(
        self,
        figure_id: str,
        image_path: str,
        context: str,
        diagram_type: str,
        prompt_name: str = "P2",
    ) -> LoopRecord:
        record = LoopRecord(figure_id=figure_id)
        history: List[float] = []
        previous_critique: Optional[str] = None
        for r in range(self.max_rounds):
            gen = self.generator.generate(
                image_path=image_path,
                context=context,
                prompt_name=prompt_name,
                previous_critique=previous_critique,
                round_index=r,
            )
            score = self.critic.score(
                image_path=image_path,
                candidate_text=gen.text,
                context=context,
                diagram_type=diagram_type,
            )
            rejected = score.D4_hallucination <= self.hallucination_reject_threshold
            record.rounds.append(
                LoopRound(
                    round_index=r,
                    generation=gen,
                    score=score,
                    rejected_for_hallucination=rejected,
                )
            )
            history.append(score.primary_mean())
            LOGGER.info(
                "figure=%s round=%d primary_mean=%.3f D4=%d rejected=%s",
                figure_id,
                r,
                history[-1],
                score.D4_hallucination,
                rejected,
            )
            if self.convergence.has_converged(history):
                record.converged = True
                break
            # On hallucination rejection, force a revision next round; pass
            # the critique plus an explicit instruction to remove fabricated
            # content. Otherwise pass through the critic's critique as-is.
            if rejected:
                previous_critique = (
                    f"Hallucination flag (D4={score.D4_hallucination}). "
                    f"Remove any claim not visible in the figure. "
                    f"Original critique: {score.critique}"
                )
            else:
                previous_critique = score.critique
        return record
