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

st.header("Top 3 Candidates")

top_candidates = candidates[:3]

for candidate in top_candidates:
    with st.container(border=True):
        st.subheader(f"Rank {candidate['rank']} — {candidate['name']}")

        final_score_column, keyword_score_column, semantic_score_column = st.columns(3)
        final_score_column.metric("Final Score", f"{candidate['final_score']:.1f}")
        keyword_score_column.metric(
            "Keyword Score", f"{candidate['keyword_score']:.1f}"
        )
        semantic_score_column.metric(
            "Semantic Score", f"{candidate['semantic_score']:.1f}"
        )

        matched_skills = candidate["matched_required_skills"]
        missing_skills = candidate["missing_required_skills"]
        matched_skills_text = ", ".join(matched_skills) or "None identified"
        missing_skills_text = ", ".join(missing_skills) or "None identified"

        matched_skills_column, missing_skills_column = st.columns(2)
        matched_skills_column.write("**Matched Required Skills**")
        matched_skills_column.write(matched_skills_text)
        missing_skills_column.write("**Missing Required Skills**")
        missing_skills_column.write(missing_skills_text)
