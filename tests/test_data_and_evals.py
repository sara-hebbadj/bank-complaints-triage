"""The data files match their documented counts and rules, and the metric helpers are right."""

import csv
import json

from bank_triage.config import DATA_DIR
from bank_triage.taxonomy import REASON_CODES, TEAMS
from evals import metrics
from evals.judge import clause_text
from evals.samples import banking77_subset, complaint_relabel_candidates


def load(name):
    return [json.loads(line) for line in (DATA_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_counts():
    assert len(load("messages.jsonl")) == 300
    assert len(load("disputes.jsonl")) == 120
    assert len(load("disputes_hard.jsonl")) == 30
    assert len(load("probes.jsonl")) == 40
    assert len(banking77_subset()) == 770 and len(complaint_relabel_candidates()) == 100


def test_gold_team_follows_the_routing_rule():
    for item in load("messages.jsonl"):
        gold = item["gold"]
        expected = ("fraud_security" if gold["fraud"] else "customer_care" if gold["vulnerable"]
                    else "disputes" if gold["is_dispute"] else gold["topic"])
        assert gold["team"] == expected and gold["team"] in TEAMS, item["id"]
        if gold["is_complaint"] or gold["fraud"]:
            assert gold["reason_code"] in REASON_CODES, item["id"]


def test_fake_data_rules():
    with (DATA_DIR / "customers.csv").open(encoding="utf-8") as handle:
        customers = list(csv.DictReader(handle))
    assert all(c["email"].endswith("@example.com") and c["phone"].startswith("+971 50 000 ") for c in customers)
    assert all(len(card) == 4 for c in customers for card in c["cards"].split("|"))


def test_every_reason_code_clause_exists_in_the_policy():
    for clause, _ in REASON_CODES.values():
        assert clause_text(clause), clause
        for language in ("ar", "fr"):
            assert f"\n{clause} " in (DATA_DIR / "policies" / f"policy_{language}.md").read_text(encoding="utf-8")


def test_relabelled_banking77_file_matches_the_sample():
    with (DATA_DIR / "banking77_complaint_labels.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["id"] for r in rows] == [r["id"] for r in complaint_relabel_candidates()]
    assert {r["is_complaint"] for r in rows} == {"0", "1"}


def test_metric_helpers():
    assert metrics.pct(1, 4) == "25.0% (1/4)" and metrics.pct(0, 0) == "n/a (0)"
    pr = metrics.precision_recall([True, True, False, False], [True, False, True, False])
    assert pr["precision"] == "50.0% (1/2)" and pr["recall"] == "50.0% (1/2)"
    assert metrics.kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0
    assert metrics.kappa([1, 1], [1, 1]) is None
    assert metrics.p50_p95([1, 2, 3, 4, 5]) == (3.0, 4.8)
