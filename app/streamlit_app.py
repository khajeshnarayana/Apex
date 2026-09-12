import sys
from html import escape
from pathlib import Path

import streamlit as st


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = REPOSITORY_ROOT / "src"
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

from stage3 import (
    compare_candidates,
    generate_comparison_explanation,
    generate_explanation,
    load_rankings,
)


RANKINGS_PATH = REPOSITORY_ROOT / "demo_data" / "mock_ranking_results.json"

DASHBOARD_CSS = """
<style>
[data-testid="stAppViewContainer"] { background: #f6f8fc; color: #1d2939; }
[data-testid="stHeader"] { background: #f6f8fc; }
[data-testid="stMainBlockContainer"] { padding-top: 2.5rem; padding-bottom: 3rem; }
[data-testid="stMain"] h1 { font-size: 2rem; letter-spacing: -.04em; }
[data-testid="stMain"] h2 { font-size: 1.4rem; letter-spacing: -.02em; }
[data-testid="stMain"] h3 { font-size: 1.1rem; }
[data-testid="stCaptionContainer"] { color: #667085; }
[data-testid="stSidebar"] { background: #101828; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] p { color: #f2f4f7; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #b8c2d5; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: .45rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: .7rem .9rem; border-radius: .55rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #293b72; box-shadow: inset 3px 0 #8098f9;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #253047; }
[data-testid="stSidebar"] button { color: #f2f4f7; }
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stExpander"] {
    background: #fff; border: 1px solid #e4e7ec !important;
    border-radius: .9rem; box-shadow: 0 2px 6px #10182804;
}
[data-testid="stMetric"] {
    background: #fff; border: 1px solid #e4e7ec; border-radius: .8rem;
    padding: 1rem; height: 100%;
}
[data-testid="stMetricLabel"] { color: #667085; }
[data-testid="stMetricValue"] {
    color: #344bc4; font-size: 1.65rem; font-weight: 650;
}
[data-testid="stMetricValue"] > div { white-space: normal; overflow-wrap: anywhere; }
[data-testid="stDataFrame"] { border-radius: .7rem; overflow: hidden; }
.apex-skills { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .75rem; }
.apex-skill {
    display: inline-block; padding: .25rem .65rem; border-radius: 999px;
    font-size: .8rem; line-height: 1.5; background: #f2f4f7;
    color: #344054; border: 1px solid #e4e7ec; overflow-wrap: anywhere;
}
.apex-skill.matched { background: #ecfdf3; color: #05603a; border-color: #abefc6; }
.apex-skill.missing { background: #fff1f3; color: #9f1239; border-color: #fecdd6; }
@media (max-width: 1100px) {
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stMain"] [data-testid="stColumn"] {
        min-width: min(100%, 16rem); flex: 1 1 16rem;
    }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding: 1.5rem 1rem; }
    [data-testid="stMain"] [data-testid="stColumn"] { flex-basis: 100%; }
}
</style>
"""


def format_score(score):
    """Format a normalized score without changing its stored value."""
    return f"{score * 100:.1f}%"


def format_score_difference(difference):
    """Format a normalized score delta as percentage points."""
    return f"{difference * 100:.1f} percentage points"


def matched_skill_label(match):
    if (
        match["match_type"] == "synonym"
        and match["found_as"].casefold() != match["skill"].casefold()
    ):
        return f'{match["skill"]} via "{match["found_as"]}"'
    return match["skill"]


def missing_skill_text(missing):
    if missing["semantic_hint"]:
        return (
            f"{missing['skill']} — not explicitly identified, though the resume "
            "shows broader semantic relevance."
        )
    return f"Missing: {missing['skill']}"


def render_skill_badges(label, skills, treatment="matched", empty="None identified"):
    """Render escaped, read-only skill labels with a plain empty state."""
    st.markdown(f"**{label}**")
    if not skills:
        st.write(empty)
        return
    badges = "".join(
        f'<span class="apex-skill {treatment}">{escape(skill)}</span>'
        for skill in skills
    )
    st.markdown(f'<div class="apex-skills">{badges}</div>', unsafe_allow_html=True)


def render_missing_skills(label, missing_skills, empty="None identified"):
    st.markdown(f"**{label}**")
    if not missing_skills:
        st.write(empty)
        return
    for missing in missing_skills:
        st.write(missing_skill_text(missing))


def render_score_metrics(candidate, compact=False):
    """Present recorded scores as percentages."""
    if compact:
        st.metric("Final Score", format_score(candidate["final_score"]))
        columns = st.columns(2)
        fields = (
            ("Keyword Score", "keyword_score"),
            ("Semantic Score", "semantic_score"),
        )
    else:
        columns = st.columns(3)
        fields = (
            ("Final Score", "final_score"),
            ("Keyword Score", "keyword_score"),
            ("Semantic Score", "semantic_score"),
        )
    for column, (label, field) in zip(columns, fields):
        column.metric(label, format_score(candidate[field]))


def render_candidate_card(candidate):
    with st.container(border=True):
        st.caption(f"RANK {candidate['rank']}")
        st.subheader(candidate["name"])
        render_score_metrics(candidate, compact=True)
        render_skill_badges(
            "Matched Skills",
            [matched_skill_label(match) for match in candidate["matched_skills"]],
        )
        render_missing_skills(
            "Missing Required Skills", candidate["missing_required_skills"]
        )
        st.markdown("**Why this candidate ranked here**")
        st.write(generate_explanation(candidate))


def render_dashboard(candidates):
    st.title("Smart Shortlisting Engine")
    st.caption("Explainable hybrid candidate ranking")
    total, top_name, top_score = st.columns(3)
    total.metric("Total Candidates", len(candidates))
    top_name.metric("Top Candidate", candidates[0]["name"])
    top_score.metric("Top Score", format_score(candidates[0]["final_score"]))
    st.header("Top 3 Candidates")
    top_candidates = candidates[:3]
    for column, candidate in zip(st.columns(len(top_candidates)), top_candidates):
        with column:
            render_candidate_card(candidate)


def render_rankings(candidates):
    st.title("Candidate Rankings")
    st.caption(f"{len(candidates)} candidates • Stage 2 order preserved")
    with st.container(border=True):
        ranking_rows = [
            {
                "Rank": candidate["rank"],
                "Candidate": candidate["name"],
                "Final Score": format_score(candidate["final_score"]),
                "Keyword Score": format_score(candidate["keyword_score"]),
                "Semantic Score": format_score(candidate["semantic_score"]),
            }
            for candidate in candidates
        ]
        st.dataframe(ranking_rows, hide_index=True, width="stretch")


def render_matching_details(matches):
    st.subheader("Matching Details")
    if not matches:
        st.write("No matched skills recorded.")
        return
    for match in matches:
        with st.container(border=True):
            st.markdown(f"**{escape(match['skill'])}**")
            st.write(f'Term found in resume: "{match["found_as"]}"')
            st.caption(f"{match['match_type'].title()} match")


def render_details(candidates_by_id):
    st.title("Candidate Details")
    selected_id = st.selectbox(
        "Select candidate",
        options=list(candidates_by_id),
        format_func=lambda candidate_id: candidates_by_id[candidate_id]["name"],
        key="detail_candidate",
    )
    candidate = candidates_by_id[selected_id]
    st.subheader(f"{candidate['name']} · Rank {candidate['rank']}")
    render_score_metrics(candidate)
    matched_column, missing_column = st.columns(2)
    with matched_column, st.container(border=True):
        render_skill_badges(
            "Matched Skills",
            [matched_skill_label(match) for match in candidate["matched_skills"]],
        )
    with missing_column, st.container(border=True):
        render_missing_skills(
            "Missing Required Skills", candidate["missing_required_skills"]
        )
    with st.container(border=True):
        st.subheader("Why this candidate ranked here")
        st.write(generate_explanation(candidate))
    render_matching_details(candidate["matched_skills"])


def render_comparison(candidates_by_id):
    st.title("Compare Candidates")
    selected_ids = []
    for index, (column, label) in enumerate(zip(st.columns(2), ("A", "B"))):
        with column, st.container(border=True):
            candidate_id = st.selectbox(
                f"Candidate {label}",
                options=list(candidates_by_id),
                index=1 if index == 1 and len(candidates_by_id) > 1 else 0,
                format_func=lambda value: candidates_by_id[value]["name"],
                key=f"comparison_candidate_{label.lower()}",
            )
            selected_ids.append(candidate_id)
            candidate = candidates_by_id[candidate_id]
            st.subheader(candidate["name"])
            st.caption(f"Rank {candidate['rank']}")
            render_score_metrics(candidate, compact=True)
    if selected_ids[0] == selected_ids[1]:
        st.info("Select two different candidates to compare.")
        return

    comparison = compare_candidates(
        candidates_by_id[selected_ids[0]], candidates_by_id[selected_ids[1]]
    )
    higher = comparison["higher_ranked_candidate"]
    lower = comparison["lower_ranked_candidate"]
    st.caption(f"Higher ranked candidate: {higher['name']}")
    st.subheader("Score Differences")
    rank_column, final_column, keyword_column, semantic_column = st.columns(4)
    rank_column.metric("Rank Difference", comparison["rank_difference"])
    final_column.metric(
        "Final Score Difference",
        format_score_difference(comparison["final_score_difference"]),
    )
    keyword_column.metric(
        "Keyword Score Difference",
        format_score_difference(comparison["keyword_score_difference"]),
    )
    semantic_column.metric(
        "Semantic Score Difference",
        format_score_difference(comparison["semantic_score_difference"]),
    )

    st.subheader("Skill Differences")
    for column, side in zip(st.columns(2), ("a", "b")):
        with column, st.container(border=True):
            name = comparison[f"candidate_{side}"]["name"]
            render_skill_badges(
                f"Skills only {name} matched",
                comparison[f"candidate_{side}_unique_matched_skills"],
                empty="None",
            )

    st.subheader("Missing Required Skills")
    for column, side in zip(st.columns(2), ("a", "b")):
        with column, st.container(border=True):
            render_missing_skills(
                comparison[f"candidate_{side}"]["name"],
                comparison[f"candidate_{side}_missing_required_skills"],
                empty="None",
            )
    with st.container(border=True):
        st.subheader(f"Why is {higher['name']} ranked above {lower['name']}?")
        st.write(generate_comparison_explanation(comparison))


st.set_page_config(
    page_title="Apex — Smart Shortlisting Engine",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
with st.sidebar:
    st.title("APEX")
    st.caption("Smart Shortlisting Engine")
    st.divider()
    page = st.radio(
        "Workspace",
        ("Dashboard", "Rankings", "Candidate Details", "Compare Candidates"),
        key="navigation",
    )
    st.divider()
    st.caption("Stage 3 demo — Explanation and UI layer")

try:
    candidates = load_rankings(RANKINGS_PATH)
except (OSError, UnicodeError, ValueError) as error:
    st.error(f"Unable to load candidate rankings: {error}")
    st.stop()

candidates_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
if page == "Dashboard":
    render_dashboard(candidates)
elif page == "Rankings":
    render_rankings(candidates)
elif page == "Candidate Details":
    render_details(candidates_by_id)
else:
    render_comparison(candidates_by_id)
