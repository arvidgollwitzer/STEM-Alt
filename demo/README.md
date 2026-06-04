# `demo/` - SYNTHETIC pipeline fixtures (Pending expert verification)

## Files

- `held_out_report_SIMULATED.json` - a simulated held-out report in the exact
schema `pipeline/05_evaluate.py` emits (`rounds` + `held_out`), with a
`_SYNTHETIC` banner key.
- `figures/` - the four evaluation figures rendered from the simulated report,
for layout and plumbing preview only.
- `../data/ratings/ratings_SIMULATED.jsonl` - two simulated raters per held-out
figure, schema-valid per `data/ratings/README.md`, every line tagged
`"synthetic": true`, every critique prefixed `[SYNTHETIC DEMO]`.

## Regenerate

```bash
python code/scripts/generate_synthetic_ratings.py        # writes the JSONL + report

# render the four demo figures into demo/figures/ (needs the analysis deps):
code/.venv/bin/python - <<'PY'
import importlib.util, json, pathlib
spec = importlib.util.spec_from_file_location("ef", "analysis/generate_eval_figures.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.render_all(json.load(open("demo/held_out_report_SIMULATED.json")), pathlib.Path("demo/figures"))
PY
```

