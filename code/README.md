# STEM-Alt code

The `stem_alt` Python package and its Hydra pipeline. `docs/ARCHITECTURE.md`
maps the modules; `docs/REPRODUCIBILITY.md` fixes the seed and provenance
contract.

## Install

```bash
uv sync
uv sync --extra dev          # add the test toolchain
uv sync --extra accessibility  # add axe + playwright for the release linter
```

## Run end-to-end

```bash
# 1. Validate manifest and write splits.
uv run python pipeline/01_build_corpus.py

# 2. Run the G-C loop across the calibration split.
uv run python pipeline/02_run_loop.py generator=gpt4o

# 3. Generate rating sheets, then ingest the JSONL ledger after rating.
uv run python pipeline/03_collect_human_ratings.py prepare \
  --loop-dir outputs/<run>/loop_traces \
  --sheets-dir outputs/<run>/sheets \
  --audio-dir outputs/<run>/audio

uv run python pipeline/03_collect_human_ratings.py ingest \
  --ratings-jsonl path/to/raw_ratings.jsonl \
  --out-dir outputs/<run>

# 4. DPO fine-tune the critic's LoRA adapters.
uv run python pipeline/04_train_dpo.py training=dpo

# 5. Evaluate on the held-out split.
uv run python pipeline/05_evaluate.py

# 6. Build the born-accessible release bundle.
uv run python pipeline/06_release_artefacts.py
```

## Synthetic demo (no GPU, no keys)

Exercise the pipeline and the figure renderer before the real study with seeded
synthetic fixtures:

```bash
python scripts/generate_synthetic_ratings.py    # -> data/ratings/ratings_SIMULATED.jsonl
                                                 #    + demo/held_out_report_SIMULATED.json
```

Every rating line carries `"synthetic": true` and the report a `_SYNTHETIC` banner. See `../demo/README.md`
for the figure-render command and the procedure for swapping in real data.

## Test

```bash
uv run pytest -ra
```

Every pipeline stage and every module has a focused unit suite under
`tests/`. Heavyweight integration tests (real LLaVA-Next load, real API
calls) sit behind `pytest -m integration` and stay off by default.

## Adding a new generator

1. Create `src/stem_alt/generator/my_generator.py`.
2. Register the class: `@register_generator("my_name")`.
3. Subclass `AltTextGenerator`; implement `generate(...)`.
4. Add `conf/generator/my_name.yaml`.
5. Run with `uv run python pipeline/02_run_loop.py generator=my_name`.

No edit to the factory wiring is required.