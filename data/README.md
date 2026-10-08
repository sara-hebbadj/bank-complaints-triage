# Data

Everything here is either public (Banking77, CC BY 4.0) or synthetic for the fictional "Gulf Horizon Bank".
No real customer data. The full one-page data card is in [../docs/data_card.md](../docs/data_card.md).

| File | What | Licence |
|---|---|---|
| `banking77/train.csv`, `banking77/test.csv` | Banking77 (PolyAI, Casanueva et al. 2020), unchanged copy of the original CSVs from [PolyAI-LDN/task-specific-datasets](https://github.com/PolyAI-LDN/task-specific-datasets) | CC BY 4.0 (attribution: PolyAI) |
| `banking77_complaint_labels.csv` | 100 Banking77 test messages relabelled complaint (1) / not (0) by a coding agent; Sara to check | CC BY 4.0 (derived) |
| `scenarios.py` | 100 scenarios written in English, Arabic (MSA, Gulf, Arabizi) and French, with gold labels | MIT |
| `make_data.py` | Generates the files below (seed 42): `python data/make_data.py` | MIT |
| `messages.jsonl` | 300 messages (the scenarios in 3 languages) | MIT |
| `disputes.jsonl` | 120 templated card disputes with gold fields and transaction IDs | MIT |
| `disputes_hard.jsonl` | 30 hand-written, messier disputes (slang, amounts in words, relative dates) | MIT |
| `probes.jsonl` | 40 social-engineering and prompt-injection probes | MIT |
| `customers.csv`, `transactions.csv` | 40 fake customers, 858 card transactions (last-4 digits only) | MIT |
| `policies/policy_{en,ar,fr}.md` | The fictional bank's complaints and disputes policy | MIT |

Regenerating with `python data/make_data.py` gives the same files (fixed seed). Changing a scenario or template
changes the test set: say so in RESULTS.md and re-run the evaluation.
