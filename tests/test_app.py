"""The Gradio app starts in demo mode without a key and the console works end to end."""

import importlib
import sys
from pathlib import Path

import pytest

from bank_triage import classic


@pytest.fixture
def app(monkeypatch, small_model, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_CHEAP", raising=False)
    monkeypatch.setattr(classic, "tfidf_model", lambda use_cache=True: small_model)  # fast; same class
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
    module = importlib.import_module("app")
    module = importlib.reload(module)
    module.audit.path = tmp_path / "audit.jsonl"
    return module


def test_demo_mode_without_a_key(app):
    assert app.OFFLINE and "Demo mode" in app.BANNER and app.triage.mode == "classic"


def test_submit_review_and_audit(app):
    receipt, summary, session = app.submit("C001", "I was charged twice at Corniche Cinemas on Sep 12: Dhs 136 "
                                                   "two times. My card ends in 2824.", None)
    assert "GHB-0001" in receipt and summary["team"] == "disputes" and session["count"] == 1
    masked, details, draft, team = app.show_case("GHB-0001")
    assert details["reason_code"] == "RC-DUP" and team == "disputes"
    note, *_ = app.decide("GHB-0001", "approve", draft, team, "")
    assert note.startswith("Saved: approve")
    assert app.audit.override_rate() == (0, 1)


def test_changed_draft_without_reason_is_refused(app):
    app.submit("C002", "Your call centre hung up on me twice today. Worst service ever.", None)
    case_id = list(app.CASES)[-1]
    note, *_ = app.decide(case_id, "approve", "A different text", app.CASES[case_id]["team"], "")
    assert "needs a reason" in note
