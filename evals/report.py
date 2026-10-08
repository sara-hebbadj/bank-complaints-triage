"""Build the results tables and charts from the saved runs in evals/results/ (no model calls).

  python -m evals.report        -> evals/results/summary.md, evals/results/*.png

Only files that exist are reported; a missing run shows as "not run".
"""

from __future__ import annotations

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from bank_triage import classic, guards  # noqa: E402
from bank_triage.config import DATA_DIR, EVALS_DIR  # noqa: E402

from . import metrics  # noqa: E402

RESULTS = EVALS_DIR / "results"
DAY = "2026-10-08"
LANGS = ["ar", "en", "fr"]


def summary(name: str) -> dict | None:
    path = RESULTS / f"{name}_{DAY}_summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def records(name: str) -> list[dict]:
    path = RESULTS / f"{name}_{DAY}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def table(header: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + \
        ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]


def intent_section() -> list[str]:
    rows = []
    for name, label in (("intent_tfidf", "TF-IDF + logistic regression"),
                        ("intent_embed", "Embeddings + logistic regression"),
                        ("intent_llm_cheap", "LLM, zero-shot (MODEL_CHEAP)")):
        s = summary(name)
        if s:
            rows.append([label, s.get("macro_f1_full_3080", "not run (cost cap)"), s["macro_f1_subset_770"],
                         s["accuracy_subset_770"], s["team_accuracy_subset_770"]])
    return ["## Intent on Banking77 (English)", ""] + table(
        ["System", "Macro-F1, full test (3,080)", "Macro-F1, subset (770)", "Accuracy, subset",
         "8-team accuracy, subset"], rows)


def relabel_complaints() -> list[list]:
    with (DATA_DIR / "banking77_complaint_labels.csv").open(encoding="utf-8") as handle:
        labels = list(csv.DictReader(handle))
    gold = [row["is_complaint"] == "1" for row in labels]
    rows = [["Keyword rules"] + _pr(gold, [classic.rule_complaint(row["text"]) for row in labels])]
    llm = {r["id"]: r for r in records("intent_llm_cheap")}
    if llm and all(row["id"] in llm for row in labels):
        rows.append(["LLM (MODEL_CHEAP)"] + _pr(gold, [bool(llm[row["id"]]["is_complaint"]) for row in labels]))
    return rows


def _pr(gold, predicted) -> list[str]:
    result = metrics.precision_recall(gold, predicted)
    return [result["recall"], result["precision"]]


def messages_section() -> list[str]:
    systems = (("messages_tfidf", "TF-IDF + rules"), ("messages_embed", "Embeddings + rules"),
               ("messages_llm_cheap", "LLM (MODEL_CHEAP) + rules"),
               ("messages_llm_main_first90", "LLM (MODEL_MAIN) + rules, 90"))
    routing, complaints, signals = [], [], []
    for name, label in systems:
        s = summary(name)
        if not s:
            continue
        routing.append([label] + [s[k]["routing_accuracy"] for k in ["all"] + LANGS] + [s["routing_gap_points"],
                       ", ".join(f"{k} {v}" for k, v in s["by_variety"].items())])
        complaints.append([label] + [f"{s[k]['complaint']['recall']} / {s[k]['complaint']['precision']}"
                                     for k in ["all"] + LANGS])
        signals.append([label, s["all"]["fraud_recall"], s["all"]["vulnerable_recall"], s["all"]["dispute"]["recall"],
                        s["all"]["sent_to_human_triage"], s.get("avg_cost_usd_per_message"),
                        f"{s['latency_ms_p50_p95'][0]:.0f} / {s['latency_ms_p50_p95'][1]:.0f}"])
    lines = ["## Routing and complaint detection on 300 synthetic messages (100 scenarios x AR/EN/FR)", ""]
    lines += table(["System", "Routing, all", "Arabic", "English", "French", "Gap (points)", "Arabic varieties"],
                   routing)
    lines += ["", "Complaint detection, recall / precision:", ""]
    lines += table(["System", "All (132 complaints)", "Arabic (44)", "English (44)", "French (44)"], complaints)
    lines += ["", "Complaint detection on 100 Banking77 test messages relabelled by hand (27 complaints):", ""]
    lines += table(["System", "Recall", "Precision"], relabel_complaints())
    lines += ["", "Priority signals and operations:", ""]
    lines += table(["System", "Fraud recall (42)", "Vulnerable recall (18)", "Dispute recall (51)",
                    "Sent to human triage", "Avg cost / message (US$)", "Latency p50 / p95 (ms)"], signals)
    return lines


def disputes_section() -> list[str]:
    rows = []
    for name, label in (("disputes_rules", "Regex + rules"), ("disputes_llm_cheap", "LLM (MODEL_CHEAP)")):
        s = summary(name)
        if not s:
            continue
        for part in ("templated", "hard"):
            if part in s:
                p = s[part]
                rows.append([label, f"{part} ({p['n']})", p["card_last4_exact"], p["merchant_exact"], p["amount_exact"],
                             p["transaction_date_exact"], p["dispute_reason_exact"], p["all_fields_exact"],
                             p["transaction_match"], p["dispute_detected"]])
    return ["## Dispute extraction and transaction matching", ""] + table(
        ["System", "Set", "Card last-4", "Merchant", "Amount", "Date", "Reason", "All 5 fields", "Transaction match",
         "Detected as dispute"], rows)


def system_cost_per_item(run_id: str) -> str:
    """Average cost per item of the system's own calls (triage, extract, draft), judge excluded, from traces."""
    traces = RESULTS / "traces.jsonl"
    calls = [json.loads(line) for line in traces.read_text(encoding="utf-8").splitlines() if line.strip()]
    mine = [c for c in calls if c.get("run_id") == f"{run_id}_{DAY}"]
    items = {c.get("item_id") for c in mine}
    cost = sum(c["cost_usd"] for c in mine if c["purpose"] != "judge")
    return f"{cost / len(items):.7f}" if items else "0"


def blocked_now(rows: list[dict]) -> int:
    """How many saved model drafts the CURRENT output check would block (deterministic re-check, no model call)."""
    drafts = [r["raw_draft"] for r in rows if r.get("raw_draft")]
    return sum(bool(guards.asks_for_secrets(d) or guards.promises_outcome(d)) for d in drafts)


def probes_section() -> list[str]:
    rows = []
    for name, label in (("probes_classic", "Classic (template drafts)"), ("probes_llm_cheap", "LLM (MODEL_CHEAP)")):
        s = summary(name)
        if s:
            rows.append([label, s["followed_or_leaked_final"], s["asks_for_secrets_raw"], s["forbidden_phrase_raw"],
                         s["route_hijacked"], s["complaint_suppressed"], s["drafts_blocked_by_code"],
                         f"{blocked_now(records(name))}/{s['n']}", s["injection_flag_rule"], s["injection_flag_model"],
                         s["judge_asks_for_secrets"], s["judge_follows_injection"]])
    return ["## Guardrail probes (40: OTP bait, requests for secrets, prompt injection)", ""] + table(
        ["System", "Failed, final reply", "Secrets regex on model draft", "Forbidden phrase in model draft",
         "Route hijacked", "Complaint suppressed", "Drafts blocked by code (as run)", "Blocked by current code",
         "Injection flag (rules)", "Injection flag (model)", "Judge: asks for secrets", "Judge: obeys injection"], rows)


def drafts_section() -> list[str]:
    rows = []
    for name, label in (("drafts_rules", "Rules + template"), ("drafts_llm_cheap", "LLM (MODEL_CHEAP)"),
                        ("drafts_draft-main_llm_cheap_first30", "LLM, MODEL_MAIN drafts (30)")):
        s = summary(name)
        if s:
            rows.append([label] + [s[k]["reason_code_accuracy"] for k in ["all"] + LANGS] +
                        [s["all"]["judge_faithful"], s["kappa_judge_vs_gold_code"], s["agreement_judge_vs_gold_code"],
                         s["all"]["drafts_blocked_by_code"], blocked_now(records(name)),
                         system_cost_per_item(name)])
    return ["## Reason codes and drafts (162 complaint or fraud messages = 54 scenarios x 3 languages)", ""] + table(
        ["System", "Reason code = gold, all", "Arabic", "English", "French", "Judge: faithful",
         "Kappa judge vs gold match", "Agreement", "Blocked (as run)", "Blocked by current code",
         "Avg system cost / message, judge excluded (US$)"], rows)


def human_check_section() -> list[str]:
    """Sara's blind labels on 60 drafts vs the judge (the spec's kappa). Empty until she fills the sheet."""
    sheet, key = EVALS_DIR / "reason_code_review_sheet.csv", EVALS_DIR / "reason_code_review_key.csv"
    if not sheet.exists() or not key.exists():
        return []
    with sheet.open(encoding="utf-8") as h1, key.open(encoding="utf-8") as h2:
        labels = {r["id"]: r["sara_faithful_1_or_0"].strip() for r in csv.DictReader(h1)}
        keys = {r["id"]: r for r in csv.DictReader(h2)}
    done = [i for i, v in labels.items() if v in ("0", "1") and keys.get(i, {}).get("judge_faithful") in ("0", "1")]
    title = ["## Human check of the judge (Sara's blind labels on 60 drafts)", ""]
    if not done:
        return title + ["Pending: `evals/reason_code_review_sheet.csv` has no labels yet."]
    sara = [labels[i] == "1" for i in done]
    judge = [keys[i]["judge_faithful"] == "1" for i in done]
    return title + [f"Labelled: {len(done)}/60. Agreement Sara vs judge: "
                    f"{metrics.pct(sum(a == b for a, b in zip(sara, judge, strict=True)), len(done))}; "
                    f"Cohen's kappa {metrics.kappa(sara, judge)}."]


def cost_section() -> list[str]:
    traces = RESULTS / "traces.jsonl"
    if not traces.exists():
        return []
    calls = [json.loads(line) for line in traces.read_text(encoding="utf-8").splitlines() if line.strip()]
    total = sum(c["cost_usd"] for c in calls)
    by_purpose: dict[tuple, list] = {}
    for call in calls:  # every traced call, smoke runs included
        by_purpose.setdefault((call["purpose"], call["model"]), []).append(call)
    rows = [[purpose, model, len(cs), f"{sum(c['cost_usd'] for c in cs) / len(cs):.7f}",
             f"{sum(c['cost_usd'] for c in cs):.4f}",
             "{:.0f} / {:.0f}".format(*metrics.p50_p95([c["latency_ms"] for c in cs]))]
            for (purpose, model), cs in sorted(by_purpose.items())]
    lines = ["## Cost and latency (all traced calls)", "", f"Total traced spend: US${total:.4f} in {len(calls)} calls "
             "(smoke runs included).", ""]
    lines += table(["Step", "Model", "Calls", "Avg cost / call (US$)", "Total (US$)",
                    "Latency p50 / p95 (ms)"], rows)
    cheap = {p: cs for (p, m), cs in by_purpose.items() if m.startswith("openai/")}
    msgs = records("messages_llm_cheap")
    if cheap.get("triage") and msgs:
        avg = {p: sum(c["cost_usd"] for c in cs) / len(cs) for p, cs in cheap.items()}
        share_draft = sum(r["pred"]["is_complaint"] or r["pred"]["fraud"] for r in msgs) / len(msgs)
        share_dispute = sum(r["pred"]["is_dispute"] for r in msgs) / len(msgs)
        per_1000 = 1000 * (avg["triage"] + share_draft * avg.get("draft", 0) + share_dispute * avg.get("extract", 0))
        lines += ["", f"Estimated LLM cost per 1,000 messages (MODEL_CHEAP): US${per_1000:.3f} = 1,000 triage calls + "
                  f"{share_draft:.0%} drafts + {share_dispute:.0%} extractions (shares from the 300-message run)."]
    return lines


def charts() -> list[str]:
    systems = [("messages_tfidf", "TF-IDF + rules"), ("messages_embed", "Embeddings + rules"),
               ("messages_llm_cheap", "LLM (cheap) + rules")]
    found = [(label, summary(name)) for name, label in systems if summary(name)]
    if not found:
        return []
    figure, axis = plt.subplots(figsize=(7, 4))
    width = 0.8 / len(found)
    colours = ["#9aa5b1", "#5b8db8", "#1f4e79"]
    for index, (label, s) in enumerate(found):
        values = [100 * s[lang]["routing_value"] for lang in LANGS]
        bars = axis.bar([x + index * width for x in range(3)], values, width, label=label, color=colours[index])
        axis.bar_label(bars, fmt="%.0f", fontsize=8)
    axis.set_xticks([x + width * (len(found) - 1) / 2 for x in range(3)], ["Arabic", "English", "French"])
    axis.set_ylabel("Routing accuracy (%)")
    axis.set_ylim(0, 105)
    axis.set_title("Routing accuracy by language (100 messages each, 8 teams)", fontsize=10)
    axis.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    path = RESULTS / "routing_by_language.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return ["", f"![Routing accuracy by language]({path.name})"]


def main() -> None:
    lines = [f"# Results summary ({DAY})", "",
             "Built by `python -m evals.report` from the saved runs in this folder. Synthetic test items were written "
             "by the same coding agent that built the system; Arabic and French are not yet native-reviewed.", ""]
    for section in (intent_section, messages_section, disputes_section, probes_section, drafts_section,
                    human_check_section, cost_section, charts):
        lines += section() + [""]
    (RESULTS / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
