from __future__ import annotations

from models.schema import ProcessStep



def validate_recommendation(step: ProcessStep) -> list[str]:
    issues: list[str] = []

    if step.ecrs == "eliminate" and step.process_class == "operation":
        issues.append("Eliminating a transformation step may be invalid without replacement logic.")

    if step.ecrs == "rearrange" and step.process_class == "operation" and not step.predecessors:
        issues.append("Rearranging an operation without sequence context may be risky.")

    if step.ssa == "automate" and step.duration_sec < 3:
        issues.append("Very short step may not justify automation.")

    if step.process_class == "inspection" and step.ecrs == "eliminate":
        issues.append("Inspection elimination requires quality-risk justification.")

    if step.process_class == "unknown":
        issues.append("Step class is unknown, so the recommendation may be weak.")

    return issues
