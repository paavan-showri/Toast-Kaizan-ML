from __future__ import annotations



def combine_confidence(
    ontology_score: float,
    ml_score: float,
    llm_confidence: float,
    validator_penalty: float = 0.0,
) -> float:
    score = 0.35 * ontology_score + 0.35 * ml_score + 0.30 * llm_confidence
    score = max(0.0, min(1.0, score - validator_penalty))
    return round(score, 4)
