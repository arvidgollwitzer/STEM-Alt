# Reproducibility

STEM-Alt targets bit-exact reproducibility on the open-weights critic and
full provenance on the closed-API generators.

## Seeds

`stem_alt.utils.set_seed(seed)` sets:

- `random.seed`
- `os.environ["PYTHONHASHSEED"]`
- `numpy.random.seed`
- `torch.manual_seed` + `torch.cuda.manual_seed_all`
- `torch.backends.cudnn.deterministic = True`
- `torch.backends.cudnn.benchmark = False`

Every pipeline stage calls `set_seed(cfg.seed)` at entry. The DPO trainer
adds the round index so each fine-tuning round has a distinct seed.

## Config snapshot

Hydra writes the resolved config tree to
`outputs/<run>/.hydra/config.yaml`. This file is the canonical record of
the run. The answer to "what hyperparameters produced this checkpoint?"
comes from there.

## Environment recording

At the start of every pipeline stage we record:

- `python --version`
- `pip freeze` (or `uv pip freeze`) → `outputs/<run>/requirements.txt`
- GPU model and driver (from `nvidia-smi --query-gpu=name,driver_version`)
- Git commit and dirty-tree status of the source repository

These artefacts live alongside the run output, not in the source repo.

## Dataset hash

The corpus manifest is hashed at the start of stage 1 with SHA-256. The
hash is written into the `splits.json` provenance block. Any change to a
figure file or to the manifest produces a new hash, which forces the
pipeline to re-emit the splits and re-run downstream stages.

## Generators

STEM-Alt ships four generator backends: three closed-API models (GPT-4o `gpt4o`,  
Claude 3.7 Sonnet `claude`, Gemini 2.5 Pro `gemini`) and one open-weights model  
(LLaVA-Next-7B `llava_next`). The paper's experiments use the three closed-API  
generators; the open-weights backend runs the same loop offline. Each `GenerationResult` carries the model  
version string. The loop trace snapshots every output, so re-running the  
loop reuses the snapshot instead of re-calling the model. Downstream stages  
stay reproducible even when a closed API drifts. The open-weights generator  
can also be pinned at a model revision for exact reproduction. Closed-API  
access needs `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY`;  
the open-weights generator and the critic need a GPU.

## What does not reproduce

- Closed-API generation is not bit-exact across API versions. We log the
version string and snapshot the output; the snapshot is the reproducible
surface.
- Non-deterministic CUDA kernels (e.g. some attention implementations) may
cause sub-1-ULP drift. We set `torch.backends.cudnn.deterministic` and
document the residual drift in the limitations section of the paper.

