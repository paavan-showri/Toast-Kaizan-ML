from __future__ import annotations

import pandas as pd

STANDARD_COLUMNS = {
    "step_id": ["step id", "step", "id", "task id", "activity no", "step no"],
    "description": ["description", "step description", "process step", "activity description", "details"],
    "activity_raw": ["activity", "symbol", "activity type", "fpc symbol", "type"],
    "duration_sec": ["duration", "duration sec", "duration (sec)", "time", "time sec", "time (sec)", "seconds"],
    "resources": ["resource", "resources", "operator/resource", "resource(s)"],
    "predecessors": ["predecessor", "predecessors", "immediate predecessors"],
    "location": ["location", "station", "workstation", "department", "area"],
    "va_class_raw": ["va/nva", "classification", "value added", "va class", "va/nnva/nva"],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    col_map: dict[str, str] = {}
    lower_cols = {str(c).lower().strip(): c for c in df.columns}

    for target, aliases in STANDARD_COLUMNS.items():
        for alias in aliases:
            if alias in lower_cols:
                col_map[lower_cols[alias]] = target
                break

    out = df.rename(columns=col_map).copy()

    required = ["step_id", "description", "activity_raw", "duration_sec"]
    for col in required:
        if col not in out.columns:
            out[col] = None

    for col in ["resources", "predecessors", "location", "va_class_raw"]:
        if col not in out.columns:
            out[col] = ""

    out["step_id"] = out["step_id"].fillna("").astype(str).str.strip()
    out["description"] = out["description"].fillna("").astype(str).str.strip()
    out["activity_raw"] = out["activity_raw"].fillna("").astype(str).str.strip()
    out["resources"] = out["resources"].fillna("").astype(str).str.strip()
    out["predecessors"] = out["predecessors"].fillna("").astype(str).str.strip()
    out["location"] = out["location"].fillna("").astype(str).str.strip()
    out["va_class_raw"] = out["va_class_raw"].fillna("").astype(str).str.strip()

    out["duration_sec"] = pd.to_numeric(out["duration_sec"], errors="coerce").fillna(0.0)

    return out
