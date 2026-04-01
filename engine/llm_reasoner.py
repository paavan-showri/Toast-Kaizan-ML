from __future__ import annotations

import json
from typing import Callable, Optional

from models.schema import ProcessStep



def build_reasoning_prompt(
    step: ProcessStep,
    prev_step: ProcessStep | None,
    next_step: ProcessStep | None,
    step_patterns: list[dict],
) -> str:
    return f"""
You are a manufacturing process improvement expert.

Analyze this flow process chart step using only the structured data below.
Do not invent missing information.
If something is uncertain, say it is uncertain.

Current Step:
- Step ID: {step.step_id}
- Description: {step.description}
- Raw Activity: {step.activity_raw}
- Duration (sec): {step.duration_sec}
- Resources: {step.resources}
- Predecessors: {step.predecessors}
- Location: {step.location}
- Action: {step.action}
- Object: {step.obj}
- Source: {step.source}
- Destination: {step.destination}
- Process Class Scores: {step.class_scores}
- Waste Scores: {step.waste_scores}
- VA Scores: {step.va_scores}

Previous Step:
- {prev_step.description if prev_step else 'None'}

Next Step:
- {next_step.description if next_step else 'None'}

Detected Patterns:
- {step_patterns}

Tasks:
1. Generate 5W1H.
2. Recommend one ECRS decision: eliminate, combine, rearrange, simplify, or keep.
3. Recommend one SSA decision: standardize, separate, automate, or no_change.
4. Give one process-improvement recommendation.
5. Give one brief rationale.
6. Estimate a confidence score from 0 to 1.

Return valid JSON only with keys:
five_w1h, ecrs, ssa, recommendation, rationale, confidence
""".strip()



def default_reasoner(
    step: ProcessStep,
    prev_step: ProcessStep | None,
    next_step: ProcessStep | None,
    step_patterns: list[dict],
) -> dict:
    process_class = step.process_class or "unknown"
    patterns = {p["pattern"] for p in step_patterns}

    why = "To support process flow"
    if next_step:
        why = f"To enable or support the next step: {next_step.description}"

    when = "At its current position in the sequence"
    if prev_step and next_step:
        when = f"After '{prev_step.description}' and before '{next_step.description}'"
    elif prev_step:
        when = f"After '{prev_step.description}'"
    elif next_step:
        when = f"Before '{next_step.description}'"

    how_map = {
        "operation": "By performing product transformation or processing",
        "transport": "By moving material, WIP, or item between locations",
        "handling": "By manual placement, positioning, loading, or unloading",
        "inspection": "By checking, measuring, or verifying quality or condition",
        "delay": "By waiting for the next resource or action",
        "storage": "By temporarily holding material or inventory",
        "retrieve": "By collecting needed material, tool, or component",
        "documentation": "By recording or documenting process information",
        "decision": "By evaluating and selecting the next action",
        "rework": "By correcting or reprocessing earlier output",
        "unknown": "By performing the described step",
    }

    ecrs = "keep"
    ssa = "no_change"
    recommendation = "Keep the step for now and review it with more context."
    rationale = "No strong waste or improvement pattern was detected from the baseline engine."
    confidence = 0.58

    if process_class in {"delay", "storage"}:
        ecrs = "eliminate"
        recommendation = "Challenge the necessity of this step and remove it if it exists only due to waiting, queueing, or temporary holding."
        rationale = "Delay and storage usually do not create direct customer value."
        confidence = 0.76
    elif process_class == "transport":
        ecrs = "rearrange"
        recommendation = "Review sequence, layout, and point-of-use staging to reduce movement and backtracking."
        rationale = "Transport often signals layout or flow improvement opportunity rather than direct value creation."
        confidence = 0.73
    elif process_class == "retrieve":
        ecrs = "combine"
        ssa = "separate"
        recommendation = "Check whether this retrieval can be batched, pre-kitted, or moved outside the main process path."
        rationale = "Retrieval inside the main flow often creates extra interruption and can sometimes be externalized."
        confidence = 0.74
    elif process_class == "handling":
        ecrs = "simplify"
        recommendation = "Reduce motion and placement effort using better positioning, fixtures, or point-of-use organization."
        rationale = "Handling steps often improve through ergonomic and method simplification."
        confidence = 0.68
    elif process_class == "inspection":
        ecrs = "simplify"
        ssa = "standardize"
        recommendation = "Review whether the inspection can be standardized, error-proofed, or embedded in-process."
        rationale = "Inspection may be necessary, but repeated or inconsistent checking can create extra processing."
        confidence = 0.70

    if "repeated_transport" in patterns:
        ecrs = "rearrange"
        recommendation = "Consecutive transport was detected. Check layout, handoffs, and direct-flow possibilities."
        rationale = "Repeated transport strongly suggests excess movement."
        confidence = max(confidence, 0.82)
    if "storage_then_use" in patterns:
        ecrs = "eliminate"
        recommendation = "Temporary storage followed by immediate use was detected. Consider direct transfer instead of buffering."
        rationale = "Storage immediately followed by use often indicates avoidable inventory and handling."
        confidence = max(confidence, 0.84)
    if "repeated_inspection" in patterns:
        ecrs = "simplify"
        ssa = "standardize"
        recommendation = "Repeated inspection was detected. Check if quality checks can be standardized or consolidated."
        rationale = "Back-to-back inspection may indicate redundant checking or lack of standard work."
        confidence = max(confidence, 0.83)

    return {
        "five_w1h": {
            "What": step.description,
            "Why": why,
            "Where": step.location or (step.destination or "Location is not explicitly stated"),
            "When": when,
            "Who": ", ".join(step.resources) if step.resources else "Unspecified resource",
            "How": how_map.get(process_class, "By executing the described step"),
        },
        "ecrs": ecrs,
        "ssa": ssa,
        "recommendation": recommendation,
        "rationale": rationale,
        "confidence": confidence,
    }



def call_reasoner(
    step: ProcessStep,
    prev_step: ProcessStep | None,
    next_step: ProcessStep | None,
    step_patterns: list[dict],
    llm_json_fn: Optional[Callable[[str], dict]] = None,
) -> dict:
    if llm_json_fn is None:
        return default_reasoner(step, prev_step, next_step, step_patterns)

    prompt = build_reasoning_prompt(step, prev_step, next_step, step_patterns)
    result = llm_json_fn(prompt)
    if isinstance(result, str):
        return json.loads(result)
    return result
