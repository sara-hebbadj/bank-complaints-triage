"""Sentence embeddings with a small on-disk cache, so the 13,083 Banking77 texts are embedded only once.

The cache file (evals/cache/, about 60 MB) is not committed. Vectors are L2-normalised.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

import numpy as np

from .classic import normalise_rows
from .config import EVALS_DIR, model_id


class CachedEmbedder:
    def __init__(self, client, path: Path | None = None):
        self.client = client
        self.model = model_id("embed") if not getattr(client, "offline", False) else "fake-offline"
        safe_name = self.model.replace("/", "_")
        self.path = path or EVALS_DIR / "cache" / f"embeddings_{safe_name}.npz"
        self.vectors: dict[str, np.ndarray] = {}
        self.lock = threading.Lock()  # the evaluation embeds from several threads
        self.unsaved = 0
        if self.path.exists():
            with np.load(self.path) as stored:
                self.vectors = {key: stored[key] for key in stored.files}

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]

    def __call__(self, texts: list[str]) -> np.ndarray:
        with self.lock:
            missing = list(dict.fromkeys(t for t in texts if self.key(t) not in self.vectors))
            if missing:
                for text, vector in zip(missing, self.client.embed(missing), strict=True):
                    self.vectors[self.key(text)] = np.asarray(vector, dtype=np.float32)
                self.unsaved += len(missing)
                if self.unsaved >= 500:  # saving 13,000 vectors takes seconds: not after every message
                    self._save()
            return normalise_rows([self.vectors[self.key(t)] for t in texts])

    def save(self) -> None:
        with self.lock:
            self._save()

    def _save(self) -> None:
        """Write to a temporary file, then rename: a stopped run can no longer leave a broken cache."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp.npz")
        np.savez_compressed(temporary, **self.vectors)
        temporary.replace(self.path)
        self.unsaved = 0
