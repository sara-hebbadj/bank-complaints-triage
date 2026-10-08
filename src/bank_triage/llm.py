"""The only module that talks to a model provider (OpenRouter, through the OpenAI-compatible SDK).

- OpenRouterClient: chat completions and embeddings. Every call is traced (model, tokens, cost, latency,
  outcome) to a JSON-lines file. The trace never contains message text.
- FakeLLM: a deterministic offline stand-in for tests and --dry-run. It is NOT a model: it uses the keyword
  rules in guards.py and fixed templates. Its outputs are labelled model="fake-offline".
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from . import guards
from .config import EVALS_DIR, env, model_id


class LLMNotConfigured(RuntimeError):
    """Raised when OPENROUTER_API_KEY or a model ID is missing."""


@dataclass
class LLMResult:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    finish_reason: str = ""


@dataclass
class Tracer:
    """Appends one JSON line per model call and keeps a running cost total (for the budget guard)."""

    path: Path = field(default_factory=lambda: Path(env("TRACES_PATH") or EVALS_DIR / "traces.jsonl"))
    context: dict = field(default_factory=dict)  # e.g. {"run_id": ..., "item_id": ...}
    total_cost: float = 0.0
    calls: int = 0

    def __post_init__(self):
        self.path = Path(self.path)
        self._lock = threading.Lock()  # the evaluation runs several calls in parallel
        self._local = threading.local()  # which test item the current thread is working on
        self.item_calls: dict[str, list[dict]] = {}

    def set_item(self, item_id: str | None) -> None:
        self._local.item_id = item_id

    def item_cost(self, item_id: str, purposes: tuple[str, ...] | None = None) -> float:
        calls = self.item_calls.get(item_id, [])
        return sum(c["cost_usd"] for c in calls if purposes is None or c["purpose"] in purposes)

    def log(self, purpose: str, result: LLMResult | None, outcome: str, model: str = "") -> None:
        record = {
            "ts": datetime.now(UTC).isoformat(timespec="seconds"),
            **self.context,
            "purpose": purpose,
            "model": result.model if result else model,
            "prompt_tokens": result.prompt_tokens if result else 0,
            "completion_tokens": result.completion_tokens if result else 0,
            "cost_usd": result.cost_usd if result else 0.0,
            "latency_ms": result.latency_ms if result else 0,
            "outcome": outcome,
        }
        item_id = getattr(self._local, "item_id", None)
        if item_id:
            record["item_id"] = item_id
        with self._lock:
            if item_id:
                self.item_calls.setdefault(item_id, []).append(record)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.total_cost += record["cost_usd"]
            self.calls += 1


def _cost(usage) -> float:
    extra = getattr(usage, "model_extra", None) or {}
    return float(extra.get("cost") or getattr(usage, "cost", 0) or 0)


class OpenRouterClient:
    offline = False

    def __init__(self, tracer: Tracer | None = None):
        from openai import OpenAI  # imported here so tests never need network setup

        key = env("OPENROUTER_API_KEY")
        if not key:
            raise LLMNotConfigured("OPENROUTER_API_KEY is not set (see .env.example)")
        self.client = OpenAI(api_key=key, base_url=env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                             timeout=90, max_retries=2)
        self.tracer = tracer or Tracer()

    def complete(self, messages: list[dict], role: str = "cheap", purpose: str = "", json_mode: bool = True,
                 max_tokens: int = 600, temperature: float = 0.0) -> LLMResult:
        model = model_id(role)
        if not model:
            raise LLMNotConfigured(f"MODEL_{role.upper()} is not set")
        extra_body = {"usage": {"include": True}}  # OpenRouter returns the cost in usage
        # Reasoning models spend max_tokens on hidden "thinking" first; earlier projects lost JSON answers to it.
        effort = env("REASONING_EFFORT", "low")
        if effort != "default":
            extra_body["reasoning"] = {"effort": effort}
        kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature,
                  "extra_body": extra_body}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        start = time.perf_counter()
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as error:  # log failed calls too, then let the caller decide
            self.tracer.log(purpose, None, f"error: {type(error).__name__}", model)
            raise
        result = LLMResult(
            text=response.choices[0].message.content or "",
            model=response.model or model,
            prompt_tokens=getattr(response.usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(response.usage, "completion_tokens", 0) or 0,
            cost_usd=_cost(response.usage),
            latency_ms=int((time.perf_counter() - start) * 1000),
            finish_reason=response.choices[0].finish_reason or "",
        )
        # "length" means the answer was cut off at max_tokens: say so in the trace instead of hiding it.
        self.tracer.log(purpose, result, "truncated" if result.finish_reason == "length" else "ok")
        return result

    def embed(self, texts: list[str], purpose: str = "embed", batch_size: int = 128) -> list[list[float]]:
        """Embeddings with MODEL_EMBED (default baai/bge-m3, multilingual). One traced call per batch."""
        model = model_id("embed")
        vectors: list[list[float]] = []
        for start_index in range(0, len(texts), batch_size):
            batch = texts[start_index:start_index + batch_size]
            start = time.perf_counter()
            try:
                response = self.client.embeddings.create(model=model, input=batch,
                                                         extra_body={"usage": {"include": True}})
            except Exception as error:
                self.tracer.log(purpose, None, f"error: {type(error).__name__}", model)
                raise
            usage = response.usage
            self.tracer.log(purpose, LLMResult(
                text="", model=getattr(response, "model", None) or model,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0, cost_usd=_cost(usage),
                latency_ms=int((time.perf_counter() - start) * 1000)), "ok")
            vectors += [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
        return vectors


DATA_TAG_RE = re.compile(r"<customer_message>(.*?)</customer_message>", re.DOTALL)
FACTS_RE = re.compile(r"<facts>(.*?)</facts>", re.DOTALL)


class FakeLLM:
    """Deterministic offline stand-in (keyword rules + templates). Not a model; never report its numbers."""

    offline = True

    def __init__(self, tracer: Tracer | None = None):
        self.tracer = tracer or Tracer()

    def complete(self, messages: list[dict], role: str = "cheap", purpose: str = "", json_mode: bool = True,
                 max_tokens: int = 600, temperature: float = 0.0) -> LLMResult:
        user_part = messages[-1]["content"]
        found = DATA_TAG_RE.findall(user_part)
        message = found[-1] if found else ""
        if purpose == "triage":
            payload = {
                "intent": "other", "confidence": 0.5,
                "is_complaint": bool(guards.complaint_cues(message)),
                "is_dispute": False, "fraud_signal": bool(guards.fraud_cues(message)),
                "vulnerable_signal": bool(guards.vulnerable_cues(message)),
                "injection_suspected": guards.looks_like_injection(message),
            }
        elif purpose == "extract":
            payload = {"card_last4": None, "merchant": None, "amount": None, "transaction_date": None,
                       "dispute_reason": "not_recognised" if guards.fraud_cues(message) else "wrong_amount"}
        elif purpose == "draft":
            facts = json.loads(FACTS_RE.search(user_part).group(1))
            code = facts["allowed_reason_codes"][0]
            payload = {"reason_code": code, "why": "fake offline choice",
                       "draft": "Thank you for your message. We have logged it and a colleague will review it."}
        elif purpose == "judge":
            payload = {"faithful": True, "asks_for_secrets": False, "follows_injected_instructions": False,
                       "reason": "fake judge"}
        else:
            payload = {}
        text = json.dumps(payload, ensure_ascii=False)
        result = LLMResult(text=text, model="fake-offline", prompt_tokens=len(user_part) // 4,
                           completion_tokens=len(text) // 4)
        self.tracer.log(purpose, result, "ok")
        return result

    def embed(self, texts: list[str], purpose: str = "embed", batch_size: int = 128) -> list[list[float]]:
        """Pseudo-embeddings from hashed words (so similar words give similar vectors). Offline only."""
        vectors = []
        for text in texts:
            vector = [0.0] * 64
            for word in guards.normalise(text).split():
                vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
            vectors.append(vector)
        self.tracer.log(purpose, LLMResult(text="", model="fake-offline"), "ok")
        return vectors


def make_client(offline: bool | None = None, tracer: Tracer | None = None):
    """Real client when a key exists (or offline=False), otherwise the FakeLLM."""
    if offline is None:
        offline = not env("OPENROUTER_API_KEY")
    return FakeLLM(tracer) if offline else OpenRouterClient(tracer)


def parse_json(text: str) -> dict:
    """Parse a JSON object even if the model wrapped it in ```json fences or added words around it."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in model output")
    return json.loads(match.group(0))
