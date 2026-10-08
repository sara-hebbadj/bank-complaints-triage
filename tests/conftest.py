"""Shared test fixtures. Tests never use the network or a real model."""

from __future__ import annotations

import socket

import pytest

from bank_triage.classic import TfidfIntentModel, load_banking77
from bank_triage.pipeline import Triage
from bank_triage.transactions import TransactionStore


@pytest.fixture(autouse=True)
def no_network(monkeypatch, tmp_path):
    """Fail loudly if any test tries to open a network connection; keep runtime files in tmp."""
    def blocked(*args, **kwargs):
        raise RuntimeError("network access is not allowed in tests")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setenv("TRIAGE_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("TRACES_PATH", str(tmp_path / "traces.jsonl"))


@pytest.fixture(scope="session")
def small_model():
    """A fast TF-IDF model on the first 25 training examples of each intent (the real one uses all 10,003)."""
    texts, labels = load_banking77("train")
    seen: dict[str, int] = {}
    keep = []
    for text, label in zip(texts, labels, strict=True):
        if seen.get(label, 0) < 25:
            seen[label] = seen.get(label, 0) + 1
            keep.append((text, label))
    return TfidfIntentModel().fit([t for t, _ in keep], [label for _, label in keep])


@pytest.fixture(scope="session")
def store():
    return TransactionStore()


@pytest.fixture
def classic_triage(small_model, store):
    return Triage(mode="classic", intent_model=small_model, store=store)


@pytest.fixture
def make_llm_triage(small_model, store):
    """Triage in LLM mode with a fake model object that has a complete() method."""
    def factory(llm):
        return Triage(mode="llm", llm=llm, intent_model=small_model, store=store)
    return factory


def message(text: str, customer_id: str = "C001", received_at: str = "2026-10-07T10:00", item_id: str = "T1") -> dict:
    return {"id": item_id, "text": text, "customer_id": customer_id, "received_at": received_at}
