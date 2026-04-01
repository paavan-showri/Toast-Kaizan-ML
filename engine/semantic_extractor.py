from __future__ import annotations

import re

from models.schema import ProcessStep
from models.ontology import SYNONYM_MAP, ACTIVITY_SYMBOL_MAP

PREPOSITIONS_TO = ["to", "into", "onto"]
PREPOSITIONS_FROM = ["from"]
STOPWORDS = {"the", "a", "an", "part", "item", "material", "station"}



def extract_semantics(step: ProcessStep) -> ProcessStep:
    text = step.description.lower().strip()
    activity = step.activity_raw.lower().strip()
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text)

    action = None
    for w in words:
        if w in SYNONYM_MAP:
            action = w
            break

    step.action = action

    # Combine text-based and activity-symbol-based process inference
    process_class = SYNONYM_MAP.get(action)
    if not process_class:
        process_class = ACTIVITY_SYMBOL_MAP.get(activity, "unknown")
    step.process_class = process_class

    if action and action in words:
        idx = words.index(action)
        tail = [w for w in words[idx + 1:] if w not in STOPWORDS]
        step.obj = " ".join(tail[:3]) if tail else None
    else:
        tail = [w for w in words if w not in STOPWORDS]
        step.obj = " ".join(tail[:3]) if tail else None

    for prep in PREPOSITIONS_FROM:
        m = re.search(rf"\b{prep}\b\s+(.+?)(?:\bto\b|$)", text)
        if m:
            step.source = m.group(1).strip()
            break

    for prep in PREPOSITIONS_TO:
        m = re.search(rf"\b{prep}\b\s+(.+)$", text)
        if m:
            step.destination = m.group(1).strip()
            break

    return step
