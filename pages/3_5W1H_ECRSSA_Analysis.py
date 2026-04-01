from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from engine.orchestrator import run_pipeline, steps_to_dataframe  # noqa: E402
from engine.fpc_table_extractor import extract_fpc_table, looks_like_embedded_fpc  # noqa: E402

st.set_page_config(page_title="5W1H + ECRSSA Analysis", layout="wide")
st.title("5W1H + ECRSSA Analysis")
st.caption("Upload a flow process chart in CSV or Excel format.")


@st.cache_data(show_spinner=False)
def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, header=None)
    return pd.read_excel(uploaded_file, header=None)


def llm_json_fn(prompt: str) -> dict:
    """
    Optional place to connect a real LLM later.

    Expected behavior:
    - accept a single prompt string
    - return a Python dict with keys:
      five_w1h, ecrs, ssa, recommendation, rationale, confidence

    For now, the orchestrator will use its internal deterministic fallback
    if you pass None. So this function is not used by default.
    """
    raise NotImplementedError("Connect your LLM here if needed.")


uploaded = st.file_uploader("Upload FPC file", type=["xlsx", "xls", "csv"])
use_llm = st.checkbox("Use external LLM callback", value=False, help="Leave off unless you wire your own LLM function.")

if uploaded is not None:
    raw_df = read_uploaded_file(uploaded)

    if raw_df.empty or raw_df.shape[0] == 0:
        st.error("The uploaded file is empty or contains no rows.")
        st.stop()

    preview_df = raw_df
    if looks_like_embedded_fpc(raw_df):
        try:
            preview_df = extract_fpc_table(raw_df)
        except Exception:
            preview_df = raw_df

    with st.expander("Preview uploaded data", expanded=False):
        st.dataframe(preview_df, width="stretch")

    with st.spinner("Running pipeline..."):
        steps, patterns = run_pipeline(raw_df, llm_json_fn=llm_json_fn if use_llm else None)
        results_df = steps_to_dataframe(steps)
        patterns_df = pd.DataFrame(patterns)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total steps", len(results_df))
    c2.metric("Flagged for review", int(results_df["needs_review"].sum()))
    c3.metric("Avg confidence", f"{results_df['confidence'].mean():.2f}")

    st.subheader("Step-Level Results")
    st.dataframe(results_df, width="stretch")

    st.subheader("Detected Patterns")
    if patterns_df.empty:
        st.info("No high-level patterns detected by the baseline pattern engine.")
    else:
        st.dataframe(patterns_df, width="stretch")

    csv_buffer = io.StringIO()
    results_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download step-level results CSV",
        data=csv_buffer.getvalue().encode("utf-8"),
        file_name="fpc_5w1h_ecrssa_results.csv",
        mime="text/csv",
    )

    if not patterns_df.empty:
        pattern_buffer = io.StringIO()
        patterns_df.to_csv(pattern_buffer, index=False)
        st.download_button(
            "Download detected patterns CSV",
            data=pattern_buffer.getvalue().encode("utf-8"),
            file_name="fpc_detected_patterns.csv",
            mime="text/csv",
        )
else:
    st.info("Upload a file to begin analysis.")
