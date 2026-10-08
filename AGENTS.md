# Notes for coding agents working on this repo

Project P12 of Sara Hebbadj's portfolio: complaint and card-dispute triage for the fictional "Gulf Horizon Bank"
in Arabic, English and French. Sara must be able to explain every line, so keep functions short and names plain.

## Layout

- `src/bank_triage/pipeline.py`: the steps for one message (`Triage.process`) and the routing rule (`route`).
- `guards.py`, `deadlines.py`, `taxonomy.py`: the deterministic rules (masking, priority cues, output checks,
  complaint clock, teams, reason codes). **Never move these rules into a prompt.**
- `classic.py`: TF-IDF / embedding classifiers and keyword detectors (baseline and fallback).
- `llm.py`: the only place that calls a model. `FakeLLM` is for tests and `--dry-run`.
- `prompts.py`: all prompts. Change `PROMPT_VERSION` in `config.py` whenever a prompt changes.
- `graph.py` (LangGraph interrupt for the human decision) and `audit.py` (what is logged).
- `evals/`: `run.py` (tasks: intent, messages, disputes, probes, drafts), `report.py`, `judge.py`, `samples.py`.
- `data/`: Banking77 (CC BY 4.0) and synthetic data; regenerate with `python data/make_data.py` (seed 42).

## Rules

- Tests never touch the network (a fixture blocks sockets) and never need keys. Use `FakeLLM` or a small fake
  class with a `complete()` method.
- Do not edit `data/*.jsonl` by hand: change `data/scenarios.py` or `data/make_data.py` and re-run it. Changing
  the test set invalidates earlier results: say so in RESULTS.md.
- Do not tune prompts or keyword lists on the test items and then report the same items as results. If you change
  them after a run, label the new numbers "after change, same test set" and keep the old files.
- Real results go in `evals/results/`, fake ones in `evals/dry_run/`. Never copy a dry-run number into the README.
- The audit log must never contain message text, card numbers or codes (`tests/test_graph_and_audit.py`).
- `review_node` in `graph.py` must stay free of side effects before `interrupt()`.
- Keys come from `Portfolio Projects/.env` or environment variables. Never print or commit them.
- Ask Sara before creating a GitHub repo, pushing, or deploying a Space.

## Checks before you finish

```bash
pytest -q
ruff check .
python -m evals.run messages --system llm --dry-run --limit 9   # pipeline still works end to end
```
