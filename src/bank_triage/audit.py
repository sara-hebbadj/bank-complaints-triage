"""The audit log a model-risk reviewer reads: one JSON line per human decision.

What it stores: a hash of the input (never the text), the model and prompt version, the predicted label and
confidence, the reason code and policy clause, the clock, guard events, and the human decision with any
override reason.
What it deliberately does NOT store: the message text, names, full card numbers, one-time codes, the draft.
(The case queue keeps the masked text for the reviewer; in production it would have its own retention period.)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .config import runtime_dir

ACTIONS = ("approve", "edit", "reject")


def audit_record(case: dict, decision: dict) -> dict:
    team_changed = bool(decision.get("team")) and decision["team"] != case["team"]
    return {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "case_id": case["case_id"],
        "input_sha256": case["input_sha256"],
        "mode": case["mode"],
        "models": case["models"],
        "prompt_version": case["prompt_version"],
        "predicted_intent": case["intent"],
        "confidence": case["confidence"],
        "predicted_team": case["team"],
        "route_why": case["route_why"],
        "is_complaint": case["is_complaint"],
        "is_dispute": case["is_dispute"],
        "priority": case["priority"],
        "matched_txn_id": (case.get("matched_txn") or {}).get("txn_id"),
        "reason_code": case.get("reason_code"),
        "policy_clause": case.get("policy_clause"),
        "clock": case.get("clock"),
        "guard_events": case.get("events", []),
        "draft_problems": case.get("draft_problems", []),
        "human_decision": decision["action"],
        "final_team": decision.get("team") or case["team"],
        "override": decision["action"] != "approve" or team_changed,
        "override_reason": decision.get("reason", ""),
        "reviewer_id": decision.get("reviewer_id", ""),
    }


class AuditLog:
    def __init__(self, path: Path | None = None):
        self.path = path or runtime_dir() / "audit_log.jsonl"

    def write(self, case: dict, decision: dict) -> dict:
        if decision.get("action") not in ACTIONS:
            raise ValueError(f"action must be one of {ACTIONS}")
        if decision["action"] != "approve" and not decision.get("reason"):
            raise ValueError("an edit or a rejection needs an override reason")
        record = audit_record(case, decision)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def override_rate(self) -> tuple[int, int]:
        """(overrides, decisions)."""
        records = self.read()
        return sum(r["override"] for r in records), len(records)
