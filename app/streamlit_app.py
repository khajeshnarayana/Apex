"""Streamlit presentation layer for the Apex Stage 3 demo."""

from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Any

import streamlit as st


APP_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = APP_DIRECTORY.parent
SOURCE_DIRECTORY = REPOSITORY_ROOT / "src"

for import_path in (APP_DIRECTORY, SOURCE_DIRECTORY):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from stage3.comparison import (  # noqa: E402
    compare_candidates,
    generate_comparison_explanation,
)
from stage3.data_loader import load_rankings  # noqa: E402
from stage3.explanation_generator import generate_explanation  # noqa: E402
from styles import EDITORIAL_CSS  # noqa: E402


RANKINGS_PATH = REPOSITORY_ROOT / "demo_data" / "mock_ranking_results.json"
SIGNAL_NOTE_TEXT = {
    "semantic_above_keyword": (
        "Semantic relevance is stronger than explicit keyword coverage."
    ),
    "keyword_above_semantic": (
        "Explicit keyword coverage is stronger than overall semantic similarity."
    ),
}


def escape(value: Any) -> str:
    """Return escaped text for the small HTML presentation helpers."""

    return html.escape(str(value))


def format_score(value: float) -> str:
    return f"{value * 100:.1f}%"


def format_score_difference(value: float) -> str:
    return f"{value * 100:.1f} percentage points"


def matched_skill_label(skill: dict[str, str]) -> str:
    """Create the existing human-readable label for a normalized match."""

    label = skill["skill"]
    if skill["found_as"] != skill["skill"]:
        label = f'{label} (found as {skill["found_as"]})'
    return f'{label} · {skill["match_type"]}'


def missing_skill_text(skill: dict[str, Any]) -> str:
    """Create the existing human-readable label for a missing requirement."""

    semantic_hint = skill.get("semantic_hint")
    if semantic_hint:
        return f'{skill["skill"]} — semantic hint: {semantic_hint}'
    return skill["skill"]


def render_page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <header class="editorial-header">
            <p class="eyebrow">{escape(kicker)}</p>
            <h1>{escape(title)}</h1>
            <p class="dek">{escape(subtitle)}</p>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(number: str, title: str, description: str | None = None) -> None:
    description_markup = (
        f'<p class="section-description">{escape(description)}</p>' if description else ""
    )
    st.markdown(
        f"""
        <div class="section-heading">
            <span>{escape(number)}</span>
            <div><h2>{escape(title)}</h2>{description_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_strip(candidate: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="score-strip" aria-label="Candidate scores">
            <div class="score-item score-item--lead">
                <span>Overall match</span><strong>{format_score(candidate['final_score'])}</strong>
            </div>
            <div class="score-item">
                <span>Keyword</span><strong>{format_score(candidate['keyword_score'])}</strong>
            </div>
            <div class="score-item">
                <span>Semantic</span><strong>{format_score(candidate['semantic_score'])}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_matched_skills(skills: list[dict[str, Any]]) -> None:
    if not skills:
        st.markdown('<p class="empty-state">None identified</p>', unsafe_allow_html=True)
        return

    rows = []
    for skill in skills:
        found_as = (
            f'<span class="skill-found">Found as {escape(skill["found_as"])}</span>'
            if skill["found_as"] != skill["skill"]
            else '<span class="skill-found">Direct term match</span>'
        )
        rows.append(
            f'<li><span class="skill-name">{escape(skill["skill"])}</span>'
            f'{found_as}<span class="match-method">{escape(skill["match_type"])}</span></li>'
        )
    st.markdown(f'<ul class="skill-ledger">{"".join(rows)}</ul>', unsafe_allow_html=True)


def render_matched_skill_groups(skills: list[dict[str, Any]]) -> None:
    """Separate classified matches while retaining the legacy combined view."""
    if not any(skill.get("required") is not None for skill in skills):
        render_matched_skills(skills)
        return

    groups = (
        ("Required matches", [skill for skill in skills if skill.get("required") is True]),
        ("Preferred matches", [skill for skill in skills if skill.get("required") is False]),
        (
            "Classification unavailable",
            [skill for skill in skills if skill.get("required") is None],
        ),
    )
    for label, grouped_skills in groups:
        if grouped_skills:
            st.markdown(f'<p class="skill-group-label">{escape(label)}</p>', unsafe_allow_html=True)
            render_matched_skills(grouped_skills)


def render_missing_skills(skills: list[dict[str, Any]], empty_text: str = "None identified") -> None:
    if not skills:
        st.markdown(f'<p class="empty-state">{escape(empty_text)}</p>', unsafe_allow_html=True)
        return

    items = "".join(
        f'<li><span>{escape(skill["skill"])}</span>'
        + (
            "<small>Not explicitly identified · broader semantic relevance detected</small>"
            if skill.get("semantic_hint")
            else "<small>Not identified</small>"
        )
        + "</li>"
        for skill in skills
    )
    st.markdown(f'<ul class="missing-ledger">{items}</ul>', unsafe_allow_html=True)


def render_string_list(items: list[str], empty_text: str = "None") -> None:
    if not items:
        st.markdown(f'<p class="empty-state">{escape(empty_text)}</p>', unsafe_allow_html=True)
        return
    markup = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(f'<ul class="plain-ledger">{markup}</ul>', unsafe_allow_html=True)


def render_explanation(candidate: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="analysis-note">
            <p class="analysis-label">Why this candidate ranked here</p>
            <p>{escape(generate_explanation(candidate))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_signal_note(candidate: dict[str, Any]) -> None:
    signal_text = SIGNAL_NOTE_TEXT.get(candidate.get("signal_note"))
    if signal_text:
        st.markdown(
            f'<p class="signal-note">{escape(signal_text)}</p>',
            unsafe_allow_html=True,
        )


def render_candidate_feature(candidate: dict[str, Any], primary: bool = False) -> None:
    modifier = " candidate-feature--primary" if primary else ""
    st.markdown(
        f"""
        <article class="candidate-feature{modifier}">
            <div class="candidate-kicker">Rank {candidate['rank']:02d}</div>
            <h3>{escape(candidate['name'])}</h3>
            <div class="candidate-score">{format_score(candidate['final_score'])}</div>
            <p class="candidate-id">Candidate {escape(candidate['candidate_id'])}</p>
        </article>
        """,
        unsafe_allow_html=True,
    )
    render_score_strip(candidate)
    st.markdown('<p class="minor-heading">Matched skills</p>', unsafe_allow_html=True)
    render_matched_skill_groups(candidate["matched_skills"])
    st.markdown('<p class="minor-heading">Missing requirements</p>', unsafe_allow_html=True)
    render_missing_skills(candidate["missing_required_skills"])
    render_explanation(candidate)


def render_dashboard(candidates: list[dict[str, Any]]) -> None:
    render_page_header(
        "Stage 3 / Decision intelligence",
        "Candidate intelligence",
        "Explainable hybrid candidate ranking",
    )
    st.markdown(
        f"""
        <div class="briefing-strip">
            <div><span>Candidates reviewed</span><strong>{len(candidates)}</strong></div>
            <div><span>Highest fit</span><strong>{escape(candidates[0]['name'])}</strong></div>
            <div><span>Top score</span><strong>{format_score(candidates[0]['final_score'])}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section_header(
        "01", "Leading candidates", "The first three entries from the existing Stage 2 rank order."
    )
    top_candidates = candidates[:3]
    if not top_candidates:
        return

    primary_column, supporting_column = st.columns([1.35, 1], gap="large")
    with primary_column:
        render_candidate_feature(top_candidates[0], primary=True)
    with supporting_column:
        for candidate in top_candidates[1:]:
            render_candidate_feature(candidate)


def render_rankings(candidates: list[dict[str, Any]]) -> None:
    render_page_header(
        "Stage 3 / Ranked field",
        "Candidate rankings",
        "The complete Stage 2 result set, presented in its supplied rank order.",
    )
    rows = "".join(
        f"""
        <tr><td class="rank-cell">{candidate['rank']:02d}</td>
        <td><strong>{escape(candidate['name'])}</strong><small>{escape(candidate['candidate_id'])}</small></td>
        <td>{format_score(candidate['final_score'])}</td><td>{format_score(candidate['keyword_score'])}</td>
        <td>{format_score(candidate['semantic_score'])}</td></tr>
        """
        for candidate in candidates
    )
    st.markdown(
        f"""
        <div class="table-shell"><table class="ranking-table">
        <thead><tr><th scope="col">Rank</th><th scope="col">Candidate</th><th scope="col">Overall</th>
        <th scope="col">Keyword</th><th scope="col">Semantic</th></tr></thead><tbody>{rows}</tbody>
        </table></div>
        """,
        unsafe_allow_html=True,
    )


def render_matching_details(candidate: dict[str, Any]) -> None:
    st.markdown('<h3 class="subsection-title">Matching details</h3>', unsafe_allow_html=True)
    if not candidate["matched_skills"]:
        st.markdown('<p class="empty-state">No matched skills recorded.</p>', unsafe_allow_html=True)
        return
    records = []
    for skill in candidate["matched_skills"]:
        classification = {
            True: "Required skill",
            False: "Preferred skill",
            None: "Classification unavailable",
        }[skill.get("required")]
        location = (
            f'<span>Found in: {escape(skill["found_in"])}</span>'
            if skill.get("found_in")
            else ""
        )
        evidence = (
            f'<blockquote><strong>Evidence</strong>{escape(skill["evidence"])}</blockquote>'
            if skill.get("evidence")
            else ""
        )
        records.append(
            f'<article class="match-record"><h4>{escape(skill["skill"])}</h4>'
            f'<p>Matched via: <strong>{escape(skill["found_as"])}</strong></p>'
            f'<div class="match-meta"><span>{escape(skill["match_type"].title())} match</span>'
            f'{location}<span>{classification}</span></div>{evidence}</article>'
        )
    st.markdown(f'<div class="match-records">{"".join(records)}</div>', unsafe_allow_html=True)


def render_details(candidates: list[dict[str, Any]]) -> None:
    render_page_header(
        "Stage 3 / Candidate record",
        "Candidate details",
        "Inspect one ranked candidate without changing the supplied scores or evidence.",
    )
    candidate_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    selected_candidate_id = st.selectbox(
        "Select candidate",
        options=list(candidate_by_id),
        format_func=lambda candidate_id: candidate_by_id[candidate_id]["name"],
    )
    candidate = candidate_by_id[selected_candidate_id]

    st.markdown(
        f"""
        <div class="record-masthead"><span>Rank {candidate['rank']:02d}</span>
        <h2>{escape(candidate['name'])}</h2><small>{escape(candidate['candidate_id'])}</small></div>
        """,
        unsafe_allow_html=True,
    )
    render_score_strip(candidate)
    matched_column, missing_column = st.columns([1.2, 1], gap="large")
    with matched_column:
        st.markdown('<h3 class="subsection-title">Matched skills</h3>', unsafe_allow_html=True)
        render_matched_skill_groups(candidate["matched_skills"])
    with missing_column:
        st.markdown('<h3 class="subsection-title">Missing required skills</h3>', unsafe_allow_html=True)
        render_missing_skills(candidate["missing_required_skills"])
    render_explanation(candidate)
    render_matching_details(candidate)


def render_comparison_candidate(candidate: dict[str, Any], label: str) -> None:
    st.markdown(
        f"""
        <div class="comparison-person"><p>{escape(label)} · Rank {candidate['rank']:02d}</p>
        <h3>{escape(candidate['name'])}</h3><strong>{format_score(candidate['final_score'])}</strong>
        <small>Overall match</small></div>
        """,
        unsafe_allow_html=True,
    )
    render_score_strip(candidate)
    render_signal_note(candidate)
    st.markdown('<p class="minor-heading">Matched skills</p>', unsafe_allow_html=True)
    render_matched_skill_groups(candidate["matched_skills"])
    st.markdown('<p class="minor-heading">Missing requirements</p>', unsafe_allow_html=True)
    render_missing_skills(candidate["missing_required_skills"])


def render_comparison(candidates: list[dict[str, Any]]) -> None:
    render_page_header(
        "Stage 3 / Side-by-side analysis",
        "Compare candidates",
        "Read the supplied ranking signals together. No scores or ranks are recalculated here.",
    )
    candidate_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    candidate_ids = list(candidate_by_id)
    selector_a, selector_b = st.columns(2, gap="large")
    with selector_a:
        candidate_a_id = st.selectbox(
            "Candidate A", options=candidate_ids,
            format_func=lambda candidate_id: candidate_by_id[candidate_id]["name"], key="candidate_a",
        )
    with selector_b:
        candidate_b_id = st.selectbox(
            "Candidate B", options=candidate_ids, index=1 if len(candidate_ids) > 1 else 0,
            format_func=lambda candidate_id: candidate_by_id[candidate_id]["name"], key="candidate_b",
        )

    if candidate_a_id == candidate_b_id:
        st.info("Select two different candidates to compare.")
        return

    candidate_a = candidate_by_id[candidate_a_id]
    candidate_b = candidate_by_id[candidate_b_id]
    comparison = compare_candidates(candidate_a, candidate_b)

    panel_a, panel_b = st.columns(2, gap="large")
    with panel_a:
        render_comparison_candidate(candidate_a, "Candidate A")
    with panel_b:
        render_comparison_candidate(candidate_b, "Candidate B")

    st.markdown(
        f"""
        <div class="comparison-verdict"><span>Higher ranked</span>
        <strong>{escape(comparison['higher_ranked_candidate']['name'])}</strong>
        <small>{comparison['rank_difference']} position{'s' if comparison['rank_difference'] != 1 else ''} apart</small></div>
        <div class="difference-strip">
        <div><span>Overall difference</span><strong>{format_score_difference(comparison['final_score_difference'])}</strong></div>
        <div><span>Keyword difference</span><strong>{format_score_difference(comparison['keyword_score_difference'])}</strong></div>
        <div><span>Semantic difference</span><strong>{format_score_difference(comparison['semantic_score_difference'])}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section_header("01", "Skill differences")
    a_column, b_column = st.columns(2, gap="large")
    with a_column:
        st.markdown(f'<h3 class="subsection-title">Only {escape(candidate_a["name"])} matched</h3>', unsafe_allow_html=True)
        if comparison["skill_classification_available"]:
            for label, field in (
                ("Required", "candidate_a_unique_required_skills"),
                ("Preferred", "candidate_a_unique_preferred_skills"),
                ("Classification unavailable", "candidate_a_unique_unclassified_skills"),
            ):
                st.markdown(f'<p class="skill-group-label">{label}</p>', unsafe_allow_html=True)
                render_string_list(comparison[field])
        else:
            render_string_list(comparison["candidate_a_unique_matched_skills"])
    with b_column:
        st.markdown(f'<h3 class="subsection-title">Only {escape(candidate_b["name"])} matched</h3>', unsafe_allow_html=True)
        if comparison["skill_classification_available"]:
            for label, field in (
                ("Required", "candidate_b_unique_required_skills"),
                ("Preferred", "candidate_b_unique_preferred_skills"),
                ("Classification unavailable", "candidate_b_unique_unclassified_skills"),
            ):
                st.markdown(f'<p class="skill-group-label">{label}</p>', unsafe_allow_html=True)
                render_string_list(comparison[field])
        else:
            render_string_list(comparison["candidate_b_unique_matched_skills"])

    render_section_header("02", "Missing required skills")
    missing_a, missing_b = st.columns(2, gap="large")
    with missing_a:
        st.markdown(f'<p class="minor-heading">{escape(candidate_a["name"])}</p>', unsafe_allow_html=True)
        render_missing_skills(comparison["candidate_a_missing_required_skills"], "None")
    with missing_b:
        st.markdown(f'<p class="minor-heading">{escape(candidate_b["name"])}</p>', unsafe_allow_html=True)
        render_missing_skills(comparison["candidate_b_missing_required_skills"], "None")

    higher = comparison["higher_ranked_candidate"]
    lower = comparison["lower_ranked_candidate"]
    st.markdown(
        f"""
        <div class="analysis-note analysis-note--comparison">
        <p class="analysis-label">Why is {escape(higher['name'])} ranked above {escape(lower['name'])}?</p>
        <p>{escape(generate_comparison_explanation(comparison))}</p></div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Apex — Smart Shortlisting Engine", layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(EDITORIAL_CSS, unsafe_allow_html=True)

try:
    candidates = load_rankings(RANKINGS_PATH)
except (OSError, UnicodeError, ValueError) as error:
    st.error(f"Unable to load candidate rankings: {error}")
    st.stop()

with st.sidebar:
    st.markdown(
        """
        <div class="brand-lockup"><div><strong>APEX</strong><small>Candidate Intelligence</small></div></div>
        <p class="nav-caption">Workspace</p>
        """,
        unsafe_allow_html=True,
    )
    selected_page = st.radio(
        "Navigation", options=["Dashboard", "Rankings", "Candidate Details", "Compare Candidates"],
        label_visibility="collapsed",
    )
    st.markdown(
        f"""
        <div class="sidebar-status"><span>Stage 3 demo</span><strong>{len(candidates)} candidates loaded</strong>
        <small>Structured Stage 2 output</small></div>
        """,
        unsafe_allow_html=True,
    )

if selected_page == "Dashboard":
    render_dashboard(candidates)
elif selected_page == "Rankings":
    render_rankings(candidates)
elif selected_page == "Candidate Details":
    render_details(candidates)
else:
    render_comparison(candidates)
