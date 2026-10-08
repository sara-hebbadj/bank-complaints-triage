"""LangGraph wiring: triage -> human review (interrupt) -> audit.

Each message is one thread. The graph pauses at `review` until a person approves, edits or rejects in the
agent console; then `record` writes the audit log. `review` has no side effects before `interrupt()`, because
LangGraph runs an interrupted node again from its first line when it resumes.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .audit import AuditLog
from .pipeline import Triage


class CaseState(TypedDict, total=False):
    message: dict
    case: dict
    decision: dict
    audit: dict


class TriageGraph:
    def __init__(self, triage: Triage, audit: AuditLog | None = None):
        self.triage = triage
        self.audit = audit or AuditLog()
        builder = StateGraph(CaseState)
        builder.add_node("triage", self.triage_node)
        builder.add_node("review", self.review_node)
        builder.add_node("record", self.record_node)
        builder.add_edge(START, "triage")
        builder.add_edge("triage", "review")
        builder.add_edge("review", "record")
        builder.add_edge("record", END)
        self.graph = builder.compile(checkpointer=InMemorySaver())

    def triage_node(self, state: CaseState) -> dict:
        return {"case": self.triage.process(state["message"])}

    def review_node(self, state: CaseState) -> dict:
        case = state["case"]
        # Pauses here. The value is what the console shows; the resume value is the human decision.
        decision = interrupt({"case_id": case["case_id"], "team": case["team"], "draft": case.get("draft")})
        return {"decision": decision}

    def record_node(self, state: CaseState) -> dict:
        return {"audit": self.audit.write(state["case"], state["decision"])}

    # ---------- used by the app and the tests ----------
    def submit(self, message: dict) -> dict:
        """Run triage for a new message; returns the case waiting for review."""
        config = {"configurable": {"thread_id": message.get("case_id") or message["id"]}}
        self.graph.invoke({"message": message}, config)
        return self.graph.get_state(config).values["case"]

    def decide(self, case_id: str, decision: dict) -> dict:
        """Resume the paused thread with the human decision; returns the audit record."""
        config = {"configurable": {"thread_id": case_id}}
        snapshot = self.graph.get_state(config)
        if not snapshot.next:  # already decided: do nothing twice
            return {**snapshot.values.get("audit", {}), "already_decided": True}
        self.graph.invoke(Command(resume=decision), config)
        return self.graph.get_state(config).values["audit"]

    def pending(self, case_id: str) -> bool:
        return bool(self.graph.get_state({"configurable": {"thread_id": case_id}}).next)
