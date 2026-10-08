# Model risk note: Gulf Horizon Bank complaint and dispute triage (portfolio demo)

*Written 8 October 2026 by a coding agent for Sara Hebbadj's portfolio project. The bank is fictional; this note
shows the structure a bank's model-risk team would expect. All numbers come from `evals/results/` (see the README
results table for denominators and commands).*

## 1. Model inventory

| Component | Type | Version / ID | Role |
|---|---|---|---|
| Intent classifier (baseline, fallback) | TF-IDF (1-2 grams) + logistic regression, C=10 | trained on Banking77 train (10,003) | English intent -> team |
| Embedding classifier (challenger) | `baai/bge-m3` embeddings + logistic regression | MODEL_EMBED, via OpenRouter | intent -> team, any language |
| LLM triage, extraction, drafting | `openai/gpt-6-luna` (MODEL_CHEAP) | prompt version `triage-v1` | intent and flags, dispute fields, acknowledgement draft |
| LLM judge (validation only) | `google/gemini-3.8-flash` (MODEL_JUDGE) | – | faithfulness of reason codes; not used in production |
| Rules | Python | this repository | masking, fraud and vulnerable cues, routing order, clock, reason-code list, output checks |

## 2. Intended use and limits

- **Use:** sort incoming customer messages (Arabic, English, French) to one of 8 teams, flag complaints and card
  disputes, extract dispute details, start the complaint clock, and draft an acknowledgement **that a person
  approves**. Every case is reviewed by a person before anything is sent or closed.
- **Not for:** deciding refunds or chargebacks, credit decisions, replying to customers without review, judging
  fraud (it only routes to the fraud team), or any language other than Arabic, English and French.
- **Users:** complaints officers and team queues. **Affected people:** retail customers, including vulnerable ones.

## 3. Validation results (8 October 2026; synthetic and public data only)

| Area | Result | Target in BUILD_SPEC | Met? |
|---|---|---|---|
| English intent, Banking77 | macro-F1 on the same 770: TF-IDF 0.893, embeddings 0.924, LLM (zero-shot) 0.753; full 3,080: TF-IDF 0.894, embeddings 0.935 | LLM >= baseline | **No** (LLM below both) |
| Routing on 300 AR/EN/FR messages | LLM 92.3% (277/300); gap between languages 2.0 points. TF-IDF 47.0%, gap 43.0 points | gap <= 5 points | LLM yes; TF-IDF no |
| Complaint recall | LLM 97.0% (128/132) on synthetic; 92.6% (25/27) on 100 relabelled Banking77 messages | >= 0.95 | synthetic yes; Banking77 no |
| Dispute extraction | templated 120: all 5 fields 100% for both regex and LLM; hand-written 30: regex 0/30 all fields, LLM 24/30 (transaction match 30/30) | report per field | reported |
| Deadline rules | 9/9 unit tests pass | 100% | yes |
| Guardrail probes (40) | final replies: 0/40 asked for secrets, 0/40 obeyed a forbidden instruction, 0/3 complaints suppressed; **3/6 route hijacks** (keyword rule) | 0/40 | **No** (3/40) |
| Reason codes | LLM 91.4% (148/162) match gold; judge "faithful" 93.8%; kappa judge vs gold match 0.461 | report kappa (with Sara's 60 labels) | partly (Sara's labels pending) |
| Operations | about US$0.23 per 1,000 messages (MODEL_CHEAP); triage call p50 2.7 s, p95 4.3 s | report | reported |

**Validation weaknesses (be explicit):** the synthetic test items, labels and keyword lists were written by the same
coding agent that built the system; Arabic and French are not native-reviewed; one run per system; n = 100 per
language; the judge is an LLM; templated disputes are easy for regex by construction.

## 4. Monitoring (what a live deployment would track)

| Metric | How | Alert when |
|---|---|---|
| Complaint recall | weekly human sample of 100 non-complaint cases, read by a complaints officer | recall estimate < 95% |
| Language parity | routing accuracy and complaint recall per language on the weekly sample | gap > 5 points |
| Human override rate | `audit_log.jsonl`: share of edits, rejections and team changes, per team and language | > 15% or a sudden change |
| Share sent to human triage | route reason "no matching intent" / "low confidence" | doubles week on week |
| Guard events | masked secrets, blocked drafts, injection flags, model fallbacks | any fallback spike; blocked drafts > 10% |
| Clock compliance | acknowledgements overdue; cases past escalation; cases reaching the ombudsman date open | any overdue acknowledgement |
| Cost and latency | `traces.jsonl` per step | cost per 1,000 messages x2, p95 latency > 10 s |
| Data drift | intent distribution and new words in messages | new top intents or sudden shifts |

## 5. Fallback when a model is down

Each LLM step falls back automatically and records the event: triage -> TF-IDF + keyword rules, extraction ->
regex, draft -> fixed template (`tests/test_pipeline.py::test_model_outage_falls_back_to_the_classic_baseline`).
The fraud and vulnerable rules, the clock and the human review do not depend on any model. Known cost of the
fallback: Arabic and French routing drops to about one third correct (TF-IDF is English-only), so more cases go to
the human triage desk.

## 6. Known failure modes and controls

| Failure | Seen in evaluation | Control |
|---|---|---|
| Keyword rule triggered by injected text ("fraud_security") moves a case to the security team | 3/6 probes, both systems | to fix: ignore team-name words such as fraud_security before matching; human review catches it |
| Output check over-blocks honest warnings ("please don't share your OTP") | 8/40 probe drafts as run; 3/40 with the apostrophe and Arabic-negation fix | safe direction (a person writes the reply); track blocked share |
| LLM confuses near-duplicate intents (card_arrival vs card_delivery_estimate) | English intent F1 0.753 | team-level accuracy matters more (88.2%); use the embedding classifier for English |
| Reason code for "broken goods, seller refuses refund" chosen as refund-not-received | 4/162 | human review; clearer clause titles |
| Taxonomy gap: no code for a declined card | judge flagged 3 drafts | add a reason code (LEARN.md exercise 3) |
| Gulf slang "نصب" (rip-off) read as fraud by the keyword rule | 1 message | rule review with native speakers |

## 7. Data protection

Masking of full card numbers (Luhn check), OTPs and CVVs before any model call; audit log without message text;
traces without prompts. For real data: a data processing agreement with the model provider and the router,
data-residency review (UAE PDPL; DIFC and ADGM have their own laws), retention limits for the case queue, and a
DPIA. Synthetic data only in this repository.

## 8. Ownership and sign-off

| Role | Who (demo) |
|---|---|
| Model owner (accountable) | Sara Hebbadj (portfolio author) |
| Business owner (in a bank) | Head of Complaints |
| Independent validation (in a bank) | Model Risk Management |
| Sign-off status | Not signed off: portfolio demo, not for production use |

> TODO (Sara): review this note, add your own checks of 60 drafts (`evals/reason_code_review_sheet.csv`) and the
> resulting kappa, and change anything you would decide differently.
