from __future__ import annotations

import pandas as pd

from models.schema import ProcessStep


def _clean_str(value) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def _split_csv_field(value) -> list[str]:
    text = _clean_str(value)
    if not text:
        return []
    text = text.replace(";", ",")
    return [x.strip() for x in text.split(",") if x.strip() and x.strip() != "—"]


def parse_dataframe(df: pd.DataFrame) -> list[ProcessStep]:
    steps: list[ProcessStep] = []

    for idx, row in df.iterrows():
        step_id = _clean_str(row.get("step_id", "")) or str(idx + 1)

        duration_val = row.get("duration_sec", 0)
        try:
            duration = float(duration_val) if not pd.isna(duration_val) else 0.0
        except Exception:
            duration = 0.0

        step = ProcessStep(
            step_id=step_id,
            description=_clean_str(row.get("description", "")),
            activity_raw=_clean_str(row.get("activity_raw", "")),
            duration_sec=duration,
            resources=_split_csv_field(row.get("resources", "")),
            predecessors=_split_csv_field(row.get("predecessors", "")),
            location=_clean_str(row.get("location", "")) or None,
            va_class_raw=_clean_str(row.get("va_class_raw", "")) or None,
        )
        steps.append(step)

    return steps
