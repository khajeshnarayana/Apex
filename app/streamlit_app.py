import sys
from pathlib import Path

import streamlit as st


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = REPOSITORY_ROOT / "src"

if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

from stage3 import load_rankings


RANKINGS_PATH = REPOSITORY_ROOT / "demo_data" / "mock_ranking_results.json"


st.set_page_config(
    page_title="Apex — Smart Shortlisting Engine",
    layout="wide",
)

st.title("Apex")
st.subheader("Smart Shortlisting Engine")
st.write("Stage 3 demo — Explanation and UI layer")

try:
    candidates = load_rankings(RANKINGS_PATH)
except (OSError, UnicodeError, ValueError) as error:
    st.error(f"Unable to load candidate rankings: {error}")
    st.stop()

st.header("Candidate Ranking")
st.metric("Candidates", len(candidates))

ranking_rows = [
    {
        "Rank": candidate["rank"],
        "Candidate": candidate["name"],
        "Final Score": candidate["final_score"],
        "Keyword Score": candidate["keyword_score"],
        "Semantic Score": candidate["semantic_score"],
    }
    for candidate in candidates
]

st.dataframe(
    ranking_rows,
    column_config={
        "Final Score": st.column_config.NumberColumn(format="%.1f"),
        "Keyword Score": st.column_config.NumberColumn(format="%.1f"),
        "Semantic Score": st.column_config.NumberColumn(format="%.1f"),
    },
    hide_index=True,
    width="stretch",
)
