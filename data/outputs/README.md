# Outputs

Empty by design. Populated by the Hydra pipeline at run time:

```
outputs/<YYYY-MM-DD>/<HH-MM-SS>/
  loop_traces/<figure_id>.json
  ratings.jsonl
  ratings_heldout.jsonl
  dpo/round_00/...
  critic.lora.yaml
  held_out_report.json
  bundle/
```

The directory is `.gitignore`d for the source repo. The paper (LaTeX source
`paper/stem-alt.tex` and the compiled `paper/stem-alt.pdf`) lives in `paper/`,
not here.
