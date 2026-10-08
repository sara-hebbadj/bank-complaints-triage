"""Human approval with a LangGraph interrupt, and what the audit log keeps (and does not keep)."""

import json

import pytest

from bank_triage.audit import AuditLog
from bank_triage.graph import TriageGraph
from tests.conftest import message

SECRET_TEXT = "My card 4111 1111 1111 1111 was charged twice at Zest Grocery, AED 120. Unacceptable!"


@pytest.fixture
def flow(classic_triage, tmp_path):
    return TriageGraph(classic_triage, AuditLog(tmp_path / "audit.jsonl"))


def test_case_waits_for_a_human_then_is_audited(flow):
    case = flow.submit(message(SECRET_TEXT, item_id="GHB-0001"))
    assert flow.pending("GHB-0001") and case["draft"]
    record = flow.decide("GHB-0001", {"action": "approve", "reviewer_id": "tester"})
    assert record["human_decision"] == "approve" and not record["override"]
    assert not flow.pending("GHB-0001")


def test_audit_log_has_a_hash_but_no_text_or_card_number(flow):
    flow.submit(message(SECRET_TEXT, item_id="GHB-0002"))
    flow.decide("GHB-0002", {"action": "approve"})
    stored = flow.audit.path.read_text(encoding="utf-8")
    record = json.loads(stored)
    assert len(record["input_sha256"]) == 64
    assert "Zest" not in stored and "4111" not in stored and "Unacceptable" not in stored
    for key in ("models", "prompt_version", "predicted_intent", "confidence", "reason_code", "policy_clause",
                "human_decision", "override_reason"):
        assert key in record


def test_deciding_twice_does_nothing_more(flow):
    flow.submit(message(SECRET_TEXT, item_id="GHB-0003"))
    flow.decide("GHB-0003", {"action": "approve"})
    again = flow.decide("GHB-0003", {"action": "reject", "reason": "changed my mind"})
    assert again["already_decided"] and len(flow.audit.read()) == 1


def test_an_override_needs_a_reason(flow):
    flow.submit(message(SECRET_TEXT, item_id="GHB-0004"))
    with pytest.raises(ValueError):
        flow.decide("GHB-0004", {"action": "edit"})


def test_team_change_counts_as_an_override(flow):
    flow.submit(message(SECRET_TEXT, item_id="GHB-0005"))
    record = flow.decide("GHB-0005", {"action": "edit", "team": "fees_fx", "reason": "it is about a fee"})
    assert record["override"] and record["final_team"] == "fees_fx"
    assert flow.audit.override_rate() == (1, 1)
