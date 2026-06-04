# Architecture

STEM-Alt via Python package and a six-stage Hydra pipeline. The package
uses the Factory/Registry pattern throughout. Adding a new generator,
critic, trainer, or compliance rule is a one-file change.

## Top-level layout

```
code/
├── pyproject.toml
├── src/stem_alt/
│   ├── corpus/         dataset Factory/Registry + stratified split
│   ├── generator/      G Factory/Registry + closed-API generators
│   ├── critic/         C Factory/Registry + LLaVA-Next-7B + LoRA
│   ├── loop/           orchestrator + plateau detection
│   ├── training/       DPO trainer + preference-pair builder
│   ├── evaluation/     pre-registered statistical plan + bootstrap CI
│   ├── compliance/     DIAGRAM linter + WCAG validator + ETH categories
│   ├── human/          rating protocol + NVDA renderer
│   └── utils/          logging, seeding, dynamic submodule import
├── conf/               Hydra config groups
├── pipeline/           six stage scripts: corpus → loop → ratings → DPO → eval → release
└── tests/              pytest suites
```

## Factory/Registry pattern

Each submodule exposes a `<Type>Factory` lookup and a
`register_<type>(name)` decorator that adds a class to the factory map.
`utils.import_modules` walks the submodule directory at import time, so the
decorators fire without an explicit registration list.

```python
@register_generator("gpt4o")
class OpenAIGenerator(AltTextGenerator):
    def __init__(self, cfg): ...
```

```python
generator = GeneratorFactory("gpt4o")(cfg.generator)
```

A new generator is one file under `generator/`. The factory wiring needs
no edit.

## Config-driven models

Generators, critics, and trainers all accept a single `cfg` argument. The
config groups under `conf/<group>/<name>.yaml` are composed by Hydra at
startup. There are no constructor parameters beyond `cfg`.

## Loop trace

`LoopOrchestrator.run_for_figure` produces a `LoopRecord` per figure:

```
LoopRecord
├── figure_id: str
├── rounds: [LoopRound, ...]      # up to max_rounds, may stop early on plateau
│   ├── round_index: int
│   ├── generation: GenerationResult     # text + provenance
│   └── score: RubricScore               # critic's five-dim scores
├── converged: bool
└── human_score: Optional[RubricScore]   # attached at stage 3
```

The trace is the single source of truth across stages 2 → 6.

## Six-stage pipeline

| Stage | Script | Reads | Writes |
|---|---|---|---|
| 1 | `01_build_corpus.py` | `manifest.csv` | `splits.json` |
| 2 | `02_run_loop.py` | calibration split | `loop_traces/<figure_id>.json` |
| 3 | `03_collect_human_ratings.py` | loop traces | `ratings_*.jsonl` |
| 4 | `04_train_dpo.py` | loop traces + ratings | `dpo/round_NN/`, updated critic cfg |
| 5 | `05_evaluate.py` | held-out split + held-out ratings | `held_out_report.json` |
| 6 | `06_release_artefacts.py` | everything above | born-accessible bundle + WCAG check |

## Why these choices

- **Hydra** composes the config. The project sweeps generator choices,
  critic LoRA ranks, and DPO hyperparameters without code edits.
- **TRL DPO** fits the small preference set (≈2,400 pairs). DPO is
  sample-efficient on small preference sets and needs no separate
  reward-model fitting.
- **LLaVA-Next-7B + LoRA** carries the reproducibility. The open-weights
  critic anchors a re-runnable artefact; closed-API generators drift
  across versions and cannot.
- **Compliance lives in one hub.** The DIAGRAM linter and the WCAG
  validator sit together in `compliance/`. They share the ETH category
  enum, and the release pipeline runs both with a single import.
