from __future__ import annotations

from typing import Dict

from models.label_sets import PROCESS_CLASSES, LEAN_WASTES, VA_CLASSES

try:
    from sentence_transformers import SentenceTransformer, util
except Exception:  # pragma: no cover
    SentenceTransformer = None
    util = None


class EmbeddingMatcher:
    """Sentence-transformer matcher with safe fallback when package/model is unavailable."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.available = SentenceTransformer is not None
        self.model_name = model_name
        self.model = None
        self.process_emb = None
        self.waste_emb = None
        self.va_emb = None

        if self.available:
            try:
                self.model = SentenceTransformer(model_name)
                self.process_emb = self.model.encode(PROCESS_CLASSES, convert_to_tensor=True)
                self.waste_emb = self.model.encode(LEAN_WASTES, convert_to_tensor=True)
                self.va_emb = self.model.encode(VA_CLASSES, convert_to_tensor=True)
            except Exception:
                self.available = False
                self.model = None

    def _uniform_scores(self, labels: list[str]) -> Dict[str, float]:
        score = 1.0 / len(labels)
        return {label: score for label in labels}

    def match_process_class(self, text: str) -> Dict[str, float]:
        if not self.available:
            return self._uniform_scores(PROCESS_CLASSES)
        emb = self.model.encode(text, convert_to_tensor=True)
        sims = util.cos_sim(emb, self.process_emb)[0]
        return {label: float(score) for label, score in zip(PROCESS_CLASSES, sims)}

    def match_waste(self, text: str) -> Dict[str, float]:
        if not self.available:
            return self._uniform_scores(LEAN_WASTES)
        emb = self.model.encode(text, convert_to_tensor=True)
        sims = util.cos_sim(emb, self.waste_emb)[0]
        return {label: float(score) for label, score in zip(LEAN_WASTES, sims)}

    def match_va(self, text: str) -> Dict[str, float]:
        if not self.available:
            return self._uniform_scores(VA_CLASSES)
        emb = self.model.encode(text, convert_to_tensor=True)
        sims = util.cos_sim(emb, self.va_emb)[0]
        return {label: float(score) for label, score in zip(VA_CLASSES, sims)}
