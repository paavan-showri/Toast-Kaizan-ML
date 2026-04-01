from __future__ import annotations

from collections import defaultdict
from typing import Callable, Optional

import pandas as pd

from engine.normalizer import normalize_columns
from engine.parser import parse_dataframe
from engine.semantic_extractor import extract_semantics
from engine.embedding_matcher import EmbeddingMatcher
from engine.ml_classifier import MLClassifier
from engine.graph_builder import build_process_graph
from engine.pattern_detector import detect_patterns
from engine.llm_reasoner import call_reasoner
from engine.validator import validate_recommendation
from engine.confidence import combine_confidence
from models.schema import ProcessStep



def _average_score_dicts(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    keys = set(a) | set(b)
    return {k: (a.get(k, 0.0) + b.get(k, 0.0)) / 2.0 for k in keys}



def steps_to_dataframe(steps: list[ProcessStep]) -> pd.DataFrame:
    rows = []
    for step in steps:
        rows.append({
            "step_id": step.step_id,
            "description": step.description,
            "activity_raw": step.activity_raw,
            "duration_sec": step.duration_sec,
            "resources": ", ".join(step.resources),
            "predecessors": ", ".join(step.predecessors),
            "location": step.location,
            "action": step.action,
            "object": step.obj,
            "source": step.source,
            "destination": step.destination,
            "process_class": step.process_class,
            "lean_waste": step.lean_waste,
            "ecrs": step.ecrs,
            "ssa": step.ssa,
            "recommendation": step.recommendation,
            "rationale": step.rationale,
            "confidence": step.confidence,
            "needs_review": step.needs_review,
            "review_issues": " | ".join(step.review_issues),
            "What": step.five_w1h.get("What", ""),
            "Why": step.five_w1h.get("Why", ""),
            "Where": step.five_w1h.get("Where", ""),
            "When": step.five_w1h.get("When", ""),
            "Who": step.five_w1h.get("Who", ""),
            "How": step.five_w1h.get("How", ""),
        })
    return pd.DataFrame(rows)



def run_pipeline(
    df: pd.DataFrame,
    llm_json_fn: Optional[Callable[[str], dict]] = None,
) -> tuple[list[ProcessStep], list[dict]]:
    df = normalize_columns(df)
    steps = parse_dataframe(df)

    embedder = EmbeddingMatcher()
    classifier = MLClassifier()

    for step in steps:
        extract_semantics(step)

        text = step.description or step.activity_raw
        emb_class_scores = embedder.match_process_class(text)
        emb_waste_scores = embedder.match_waste(text)
        emb_va_scores = embedder.match_va(text)

        ml_class_scores = classifier.classify_process(text)
        ml_waste_scores = classifier.classify_waste(text)
        ml_va_scores = classifier.classify_va(text)

        step.class_scores = _average_score_dicts(emb_class_scores, ml_class_scores)
        step.waste_scores = _average_score_dicts(emb_waste_scores, ml_waste_scores)
        step.va_scores = _average_score_dicts(emb_va_scores, ml_va_scores)

        # Keep strong symbolic/process extraction when available
        inferred_from_text = step.process_class
        scored_class = max(step.class_scores, key=step.class_scores.get)
        step.process_class = inferred_from_text if inferred_from_text and inferred_from_text != "unknown" else scored_class
        step.lean_waste = max(step.waste_scores, key=step.waste_scores.get)

    graph = build_process_graph(steps)
    patterns = detect_patterns(graph)
    patterns_by_step: dict[str, list[dict]] = defaultdict(list)
    for pattern in patterns:
        for sid in pattern["steps"]:
            patterns_by_step[str(sid)].append(pattern)

    for i, step in enumerate(steps):
        prev_step = steps[i - 1] if i > 0 else None
        next_step = steps[i + 1] if i < len(steps) - 1 else None
        step_patterns = patterns_by_step.get(step.step_id, [])

        reasoned = call_reasoner(step, prev_step, next_step, step_patterns, llm_json_fn=llm_json_fn)

        step.five_w1h = reasoned.get("five_w1h", {})
        step.ecrs = reasoned.get("ecrs", "keep")
        step.ssa = reasoned.get("ssa", "no_change")
        step.recommendation = reasoned.get("recommendation", "")
        step.rationale = reasoned.get("rationale", "")
        llm_conf = float(reasoned.get("confidence", 0.5))

        issues = validate_recommendation(step)
        step.review_issues = issues
        step.needs_review = bool(issues)

        ontology_score = max(step.class_scores.values()) if step.class_scores else 0.0
        ml_score = ontology_score
        penalty = 0.15 if step.needs_review else 0.0
        step.confidence = combine_confidence(ontology_score, ml_score, llm_conf, penalty)

    return steps, patterns
