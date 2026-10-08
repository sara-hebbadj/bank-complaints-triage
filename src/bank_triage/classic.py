"""Classical models: no LLM, cheap, fast, and the fallback when the LLM is down.

- IntentModel: TF-IDF (word 1-2 grams) + logistic regression, or logistic regression on embeddings,
  trained on the Banking77 training split (10,003 English messages, 77 intents, CC BY 4.0).
- rule_complaint() / rule_dispute(): keyword rules in Arabic, English and French.

The model settings were chosen once, before any test run, and not tuned on the test set.
"""

from __future__ import annotations

import csv
import pickle

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from . import extract, guards
from .config import DATA_DIR, runtime_dir


def load_banking77(split: str) -> tuple[list[str], list[str]]:
    """split 'train' (10,003) or 'test' (3,080) -> (texts, intent labels)."""
    with (DATA_DIR / "banking77" / f"{split}.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row["text"] for row in rows], [row["category"] for row in rows]


class TfidfIntentModel:
    name = "tfidf"

    def __init__(self):
        self.pipeline = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                                      LogisticRegression(C=10, max_iter=2000))

    def fit(self, texts: list[str], labels: list[str]) -> TfidfIntentModel:
        self.pipeline.fit(texts, labels)
        return self

    def predict(self, texts: list[str]) -> list[tuple[str, float]]:
        """(intent, probability of that intent) for each text."""
        probabilities = self.pipeline.predict_proba(texts)
        classes = self.pipeline.classes_
        return [(classes[row.argmax()], float(row.max())) for row in probabilities]


class EmbeddingIntentModel:
    """Logistic regression on sentence embeddings (multilingual, so it can be tried on Arabic and French)."""

    name = "embed"

    def __init__(self, embed_fn):
        self.embed_fn = embed_fn  # list[str] -> np.ndarray (n, d), L2-normalised
        self.classifier = LogisticRegression(C=10, max_iter=3000)

    def fit(self, texts: list[str], labels: list[str]) -> EmbeddingIntentModel:
        self.classifier.fit(self.embed_fn(texts), labels)
        return self

    def predict(self, texts: list[str]) -> list[tuple[str, float]]:
        probabilities = self.classifier.predict_proba(self.embed_fn(texts))
        classes = self.classifier.classes_
        return [(classes[row.argmax()], float(row.max())) for row in probabilities]


def tfidf_model(use_cache: bool = True) -> TfidfIntentModel:
    """Train on Banking77 train (about 10 seconds), cached in runtime/ so the demo starts fast."""
    cache = runtime_dir() / "tfidf_intent_model.pkl"
    if use_cache and cache.exists():
        with cache.open("rb") as handle:
            return pickle.load(handle)  # our own file, written below; never load pickles from elsewhere
    model = TfidfIntentModel().fit(*load_banking77("train"))
    if use_cache:
        with cache.open("wb") as handle:
            pickle.dump(model, handle)
    return model


def normalise_rows(vectors) -> np.ndarray:
    array = np.asarray(vectors, dtype=np.float32)
    return array / np.clip(np.linalg.norm(array, axis=1, keepdims=True), 1e-9, None)


def rule_dispute(text: str) -> bool:
    """A dispute names a reason (charged twice, not received...) and an amount."""
    return extract.rule_reason(text) is not None and extract.rule_amount(text) is not None


def rule_complaint(text: str) -> bool:
    return bool(guards.complaint_cues(text)) or rule_dispute(text)
