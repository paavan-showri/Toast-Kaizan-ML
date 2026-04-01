
from __future__ import annotations

import pandas as pd

EXPECTED_HEADER = {
    "step": "step_id",
    "description": "description",
    "activity": "activity_raw",
    "start time": "start_time",
    "end time": "end_time",
    "duration (sec)": "duration_sec",
    "activity type": "va_class_raw",
    "resources": "resources",
}


def _clean_cell(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if s.lower() == 'nan':
        return ""
    return s


def _duration_to_sec(x) -> float:
    x = _clean_cell(x)
    if not x:
        return 0.0
    parts = x.split(':')
    if len(parts) == 3:
        try:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            return 0.0
    try:
        return float(x)
    except Exception:
        return 0.0


def looks_like_embedded_fpc(df: pd.DataFrame) -> bool:
    sample_rows = min(len(df), 25)
    for i in range(sample_rows):
        row_vals = [_clean_cell(v).lower() for v in df.iloc[i].tolist()]
        if 'step' in row_vals and 'description' in row_vals and 'activity' in row_vals:
            return True
    return False


def extract_fpc_table(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy().fillna('')
    header_row_idx = None

    for i in range(len(df)):
        row_vals = [_clean_cell(v).lower() for v in df.iloc[i].tolist()]
        if 'step' in row_vals and 'description' in row_vals and 'activity' in row_vals:
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError('Could not find the embedded FPC header row.')

    header_vals = [_clean_cell(v) for v in df.iloc[header_row_idx].tolist()]
    data = df.iloc[header_row_idx + 1 :].copy()
    data.columns = header_vals
    data = data.loc[:, [_clean_cell(c) != '' for c in data.columns]].copy()

    # keep only rows that look like real numeric steps
    if 'Step' not in data.columns:
        step_col = next((c for c in data.columns if _clean_cell(c).lower() == 'step'), None)
        if step_col is None:
            raise ValueError("Embedded FPC table found, but 'Step' column is missing.")
    data['Step'] = data['Step'].astype(str).str.strip()
    data = data[data['Step'].str.match(r'^\d+$', na=False)].copy()

    rename_map = {}
    for col in data.columns:
        key = _clean_cell(col).lower()
        if key in EXPECTED_HEADER:
            rename_map[col] = EXPECTED_HEADER[key]

    data = data.rename(columns=rename_map)

    for col in ['step_id', 'description', 'activity_raw', 'duration_sec', 'resources', 'va_class_raw']:
        if col not in data.columns:
            data[col] = ''

    data['duration_sec'] = data['duration_sec'].apply(_duration_to_sec)
    data['step_id'] = data['step_id'].astype(str).str.strip()
    data['description'] = data['description'].astype(str).str.strip()
    data['activity_raw'] = data['activity_raw'].astype(str).str.strip()
    data['resources'] = data['resources'].astype(str).str.strip()
    data['va_class_raw'] = data['va_class_raw'].astype(str).str.strip()

    return data.reset_index(drop=True)
