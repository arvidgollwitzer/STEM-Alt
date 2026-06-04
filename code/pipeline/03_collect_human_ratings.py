"""Stage 3: prepare and ingest dual-rater human ratings.

Two phases:
  prepare: generate rating sheets for the calibration figures plus
           pre-rendered NVDA audio (offline mode by default).
  ingest:  read a `ratings/*.jsonl` directory and attach H-scores to
           loop traces. Enforces two-rater coverage.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

from stem_alt.critic.rubric import RubricScore
from stem_alt.human import HumanRatingProtocol, NVDARenderer, RaterRole, RatingRecord
from stem_alt.utils import get_logger

LOGGER = get_logger(__name__)


def prepare(loop_dir: Path, sheets_dir: Path, audio_dir: Path) -> None:
    renderer = NVDARenderer(mode="offline", offline_tts_command="espeak-ng")
    sheets_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    for trace_path in sorted(loop_dir.glob("*.json")):
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        figure_id = trace["figure_id"]
        final_round = trace["rounds"][-1]
        final_text = final_round["generation"]["text"]
        audio_path = audio_dir / f"{figure_id}.wav"
        try:
            renderer.render(final_text, out_path=audio_path)
        except RuntimeError as exc:  # NVDA / TTS not installed in CI
            LOGGER.warning("Skipped audio for %s: %s", figure_id, exc)
        sheet = {
            "figure_id": figure_id,
            "candidate_round": final_round["round_index"],
            "candidate_text": final_text,
            "audio_path": str(audio_path),
            "rubric_dimensions": [
                "D1_factual_correctness",
                "D2_information_sufficiency",
                "D3_domain_accuracy",
                "D4_hallucination",
                "D5_conciseness",
            ],
            "instructions": (
                "Rate each dimension 1-5. Listen to the audio first if you are a "
                "screen-reader-user rater. Add a one-paragraph critique."
            ),
        }
        (sheets_dir / f"{figure_id}.json").write_text(
            json.dumps(sheet, indent=2) + "\n", encoding="utf-8"
        )


def ingest(ratings_jsonl: Path, out_dir: Path) -> Path:
    proto = HumanRatingProtocol(out_dir=out_dir)
    with ratings_jsonl.open("r", encoding="utf-8") as fh:
        for line in fh:
            payload = json.loads(line)
            score = RubricScore(**payload["score"])
            proto.add(
                RatingRecord(
                    figure_id=payload["figure_id"],
                    rater_id=payload["rater_id"],
                    rater_role=RaterRole(payload["rater_role"]),
                    candidate_round=int(payload["candidate_round"]),
                    score=score,
                    rendered_via_nvda=bool(payload.get("rendered_via_nvda", False)),
                    timestamp=payload.get(
                        "timestamp", _dt.datetime.utcnow().isoformat()
                    ),
                )
            )
    path = proto.save()
    LOGGER.info(
        "Ingested %d ratings. %d figures have two raters.",
        len(proto.records),
        proto.budget_used(),
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_prep = sub.add_parser("prepare")
    p_prep.add_argument("--loop-dir", type=Path, required=True)
    p_prep.add_argument("--sheets-dir", type=Path, required=True)
    p_prep.add_argument("--audio-dir", type=Path, required=True)
    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("--ratings-jsonl", type=Path, required=True)
    p_ing.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "prepare":
        prepare(args.loop_dir, args.sheets_dir, args.audio_dir)
    else:
        ingest(args.ratings_jsonl, args.out_dir)


if __name__ == "__main__":
    main()
