# Dry runs: NOT results

Files here come from `python -m evals.run <task> --system llm --dry-run`, which uses `FakeLLM`, a keyword-rule
stand-in, instead of a model. They only prove that the pipeline runs end to end without a key. Never quote a
number from this folder; real results are in `../results/`.
