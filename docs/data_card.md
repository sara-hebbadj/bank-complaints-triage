# Data card (one page)

**Purpose.** Train and test a triage system for bank customer messages in Arabic, English and French: intent and
team routing, complaint and dispute detection, dispute field extraction, reason codes and guardrails. No real
customer data is used anywhere.

## Sources

| Dataset | Size | Source and licence | Who wrote it | Used for |
|---|---|---|---|---|
| Banking77 | 13,083 English queries, 77 intents (10,003 train / 3,080 test) | PolyAI, [github.com/PolyAI-LDN/task-specific-datasets](https://github.com/PolyAI-LDN/task-specific-datasets), **CC BY 4.0** (Casanueva et al., 2020). Copied unchanged into `data/banking77/` | PolyAI annotators | Training the classical models; English intent test |
| Complaint relabels | 100 Banking77 test messages | Same licence (derived labels) | Coding agent (Claude), 8 Oct 2026; **to be checked by Sara** | Complaint precision/recall on public text |
| Synthetic messages | 300 = 100 scenarios x (Arabic, English, French) | MIT, this repo (`data/scenarios.py`) | Coding agent; Arabic and French **not yet native-reviewed** | Routing, complaint detection, language parity, reason codes |
| Templated disputes | 120 (40 per language) | MIT (`data/make_data.py`, seed 42) | Generated from templates | Field extraction, transaction matching |
| Hand-written hard disputes | 30 (10 per language) | MIT (`make_data.py`, `HARD`) | Coding agent, written after the regex baseline was frozen | Extraction on messy text |
| Probes | 40 (14 EN, 13 AR, 13 FR) | MIT (`make_data.py`, `PROBES`) | Coding agent | Guardrails: OTP bait, requests for secrets, prompt injection |
| Customers and transactions | 40 customers, 858 card transactions (Aug-Oct 2026) | MIT | Generated, seed 42 | Dispute matching in DuckDB |
| Policy | Complaints and disputes policy in EN/AR/FR, 11 sections | MIT (`data/policies/`) | Coding agent; the bank and its targets are fictional | Reason codes and clauses |

## Labels

- **Team (8):** fraud first, then vulnerable customer, then card dispute, then the topic team (the same order as
  the routing rule in code). Banking77 intents map to teams in `taxonomy.py`.
- **Complaint:** dissatisfaction with something the bank did or failed to do, with a fix, refund or answer expected.
  A neutral question is not a complaint. Every card dispute is a complaint (policy 5.1). Borderline cases are
  noted in `banking77_complaint_labels.csv`.
- **Reason code:** one of 14 codes, each tied to one policy clause.

## Distribution (synthetic messages, per language)

| | Count of 100 |
|---|---|
| Teams | cards 13, payments 13, ATM and cash 9, fees and FX 12, disputes 15, fraud and security 14, accounts and KYC 12, customer care 12 |
| Complaints | 44 (of which card or ATM disputes 17) |
| Fraud reports | 14 · vulnerable customers 6 · with a reason code 54 |
| Arabic varieties | Modern Standard 57, Gulf dialect 34, Arabizi 9 |

## Fake-data rules

Fake names; `@example.com` e-mails; `+971 50 000 xxxx` phones; card **last-4 digits only** (no full card number
exists in the data); fictional merchants ("Desert Bloom Café", "StreamMax"...) and a fictional bank.
Test strings that look like card numbers in `tests/` are the standard Visa test number 4111 1111 1111 1111.

## Known limits

- The same coding agent wrote the scenarios, labels, keyword lists, templates and the system, on the same day.
  This favours the keyword rules (they were written with the scenarios in view) and makes the templated disputes
  easy for the regex baseline. The 30 hard disputes were added to reduce this.
- Arabic and French texts are machine-written and not yet reviewed by a native speaker; dialect coverage is thin
  (Gulf only, 34 + 9 Arabizi messages).
- Banking77 is English and from a UK-style fintech; intent names do not match a UAE bank's products exactly.
- Merchant names in disputes are in Latin script except in the hard set, where some are in Arabic script.
