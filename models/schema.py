from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class ProcessStep:
    step_id: str
    description: str
    activity_raw: str
    duration_sec: float
    resources: List[str] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    location: Optional[str] = None
    va_class_raw: Optional[str] = None

    # extracted semantics
    action: Optional[str] = None
    obj: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    process_class: Optional[str] = None
    lean_waste: Optional[str] = None
    therblig: Optional[str] = None

    # scores
    class_scores: Dict[str, float] = field(default_factory=dict)
    waste_scores: Dict[str, float] = field(default_factory=dict)
    va_scores: Dict[str, float] = field(default_factory=dict)

    # reasoning output
    five_w1h: Dict[str, str] = field(default_factory=dict)
    ecrs: Optional[str] = None
    ssa: Optional[str] = None
    recommendation: Optional[str] = None
    rationale: Optional[str] = None

    # control
    confidence: float = 0.0
    needs_review: bool = False
    review_issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
