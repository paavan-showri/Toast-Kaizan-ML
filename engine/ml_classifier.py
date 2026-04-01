from __future__ import annotations

from typing import Dict, Iterable

from models.label_sets import PROCESS_CLASSES, LEAN_WASTES, VA_CLASSES

try:
    from transformers import pipeline
except Exception:  # pragma: no cover
    pipeline = None


class MLClassifier:
    """Zero-shot classifier with deterministic fallback and empty-text protection."""

    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.available = pipeline is not None
        self.zero_shot = None
        if self.available:
            try:
                self.zero_shot = pipeline("zero-shot-classification", model=model_name)
            except Exception:
                self.available = False
                self.zero_shot = None

    def _safe_text(self, text) -> str:
        if text is None:
            return ""
        text = str(text).strip()
        if text.lower() == "nan":
            return ""
        return text

    def _uniform_scores(self, labels: Iterable[str]) -> Dict[str, float]:
        labels = list(labels)
        if not labels:
            return {}
        score = 1.0 / len(labels)
        return {label: score for label in labels}

    def _classify(self, text: str, labels: list[str]) -> Dict[str, float]:
        text = self._safe_text(text)
        if not labels:
            return {}
        if not self.available or not text:
            return self._uniform_scores(labels)
        try:
            result = self.zero_shot(text, labels, multi_label=False)
            return dict(zip(result["labels"], result["scores"]))
        except Exception:
            return self._uniform_scores(labels)

    def classify_process(self, text: str) -> Dict[str, float]:
        return self._classify(text, PROCESS_CLASSES)

    def classify_waste(self, text: str) -> Dict[str, float]:
        return self._classify(text, LEAN_WASTES)

    def classify_va(self, text: str) -> Dict[str, float]:
        return self._classify(text, VA_CLASSES)
