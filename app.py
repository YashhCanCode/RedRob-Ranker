"""Minimal hosted-sandbox demo (Streamlit) for the Redrob ranker.

Satisfies the mandatory 'sandbox / demo link' requirement: upload a small
candidate sample (<=100 candidates, .jsonl) and get a ranked CSV back, produced
by the exact same offline pipeline used for the full submission.

Deploy free on HuggingFace Spaces or Streamlit Cloud:
  1. Push this repo to GitHub.
  2. New Streamlit Space -> point at the repo -> app file `app.py`.
  3. requirements: numpy, scikit-learn, PyYAML, streamlit, pandas.
"""
import io, json, tempfile, os, sys
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import run

st.set_page_config(page_title="Redrob Candidate Ranker", layout="wide")
st.title("Redrob Candidate Ranker — sandbox demo")
st.caption("Small-sample sandbox demo of the offline, CPU-only hybrid ranker for the "
           "Senior AI Engineer JD. Upload a candidates.jsonl sample (up to ~100 rows) or "
           "use the bundled 50-candidate sample. The full 100k -> top-100 ranking is "
           "produced by rank.py; this page just proves the engine runs.")

up = st.file_uploader("candidates.jsonl", type=["jsonl"])
sample_path = os.path.join(os.path.dirname(__file__), "sample", "sample_candidates.jsonl")
use_sample = st.checkbox("Use bundled 50-candidate sample", value=not up)

if st.button("Rank candidates"):
    if use_sample:
        path = sample_path
    elif up:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl", mode="wb")
        tmp.write(up.read()); tmp.close(); path = tmp.name
    else:
        st.warning("Upload a file or tick the sample box."); st.stop()

    n = sum(1 for _ in open(path))
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
    with st.spinner(f"Ranking {n} candidates..."):
        run(path, out, top_n=min(100, n), log=lambda *a, **k: None)
    df = pd.read_csv(out)
    st.success(f"Ranked {len(df)} candidates.")
    st.dataframe(df, use_container_width=True)
    st.download_button("Download submission.csv", open(out, "rb").read(),
                       file_name="submission.csv", mime="text/csv")
