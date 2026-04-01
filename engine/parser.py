from __future__ import annotations

import pandas as pd

from models.schema import ProcessStep


def _split_csv_field(value) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    text = text.replace(";", ",")
    return [x.strip() for x in text.split(",") if x.strip() and x.strip() != "—"]



def parse_dataframe(df: pd.DataFrame) -> list[ProcessStep]:
    steps: list[ProcessStep] = []

    for idx, row in df.iterrows():
        step_id = str(row.get("step_id", "")).strip() or str(idx + 1)
        step = ProcessStep(
            step_id=step_id,
            description=str(row.get("description", "")).strip(),
            activity_raw=str(row.get("activity_raw", "")).strip(),
            duration_sec=float(row.get("duration_sec") or 0.0),
            resources=_split_csv_field(row.get("resources", "")),
            predecessors=_split_csv_field(row.get("predecessors", "")),
            location=str(row.get("location", "")).strip() or None,
            va_class_raw=str(row.get("va_class_raw", "")).strip() or None,
        )
        steps.append(step)

    return steps
