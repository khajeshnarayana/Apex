"""Generate deterministic explanations from normalized Stage 2 output."""

from typing import Any


def _format_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _format_score(score: float) -> str:
    return f"{score * 100:.1f}%"


def generate_explanation(candidate: dict[str, Any]) -> str:
    """Explain only the normalized matches, gaps, and recorded Stage 2 scores."""
    matched_phrases = []
    for match in candidate["matched_skills"]:
        phrase = match["skill"]
        if (
            match["match_type"] == "synonym"
            and match["found_as"].casefold() != match["skill"].casefold()
        ):
            phrase = f"{match['skill']} via {match['found_as']}"
        matched_phrases.append(phrase)

    parts = []
    if matched_phrases:
        parts.append(f"Matched skills include {_format_list(matched_phrases)}.")
    else:
        parts.append("No matched skills were recorded.")

    missing_skills = candidate["missing_required_skills"]
    if missing_skills:
        for missing in missing_skills:
            if missing["semantic_hint"]:
                parts.append(
                    f"{missing['skill']} was not explicitly identified, though the "
                    "resume shows broader semantic relevance."
                )
            else:
                parts.append(f"{missing['skill']} was not explicitly identified.")
    else:
        parts.append("No required skills were identified as missing.")

    parts.append(
        f"The candidate recorded a {_format_score(candidate['final_score'])} final "
        f"score, with {_format_score(candidate['keyword_score'])} keyword matching "
        f"and {_format_score(candidate['semantic_score'])} semantic similarity."
    )
    return " ".join(parts)
