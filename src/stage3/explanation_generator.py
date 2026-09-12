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


def _match_phrase(match: dict[str, Any]) -> str:
    phrase = match["skill"]
    if (
        match["match_type"] == "synonym"
        and match["found_as"].casefold() != match["skill"].casefold()
    ):
        phrase = f"{match['skill']} via {match['found_as']}"
    return phrase


def _evidence_sentences(matches: list[dict[str, Any]]) -> list[str]:
    """Select at most two evidence excerpts, preferring required matches."""
    evidence_matches = [
        match
        for classification in (True, None, False)
        for match in matches
        if match.get("evidence") and match.get("required") is classification
    ]

    sentences = []
    for match in evidence_matches[:2]:
        location = (
            f" from the {match['found_in']} section" if match.get("found_in") else ""
        )
        sentences.append(
            f"Evidence for {match['skill']}{location}: \"{match['evidence']}\"."
        )
    return sentences


def generate_explanation(candidate: dict[str, Any]) -> str:
    """Explain only the normalized matches, gaps, and recorded Stage 2 scores."""
    matches = candidate["matched_skills"]
    required_matches = [match for match in matches if match.get("required") is True]
    preferred_matches = [match for match in matches if match.get("required") is False]
    unclassified_matches = [
        match for match in matches if match.get("required") is None
    ]
    classification_available = bool(required_matches or preferred_matches)
    parts = []
    if classification_available:
        if required_matches:
            parts.append(
                "Matched required skills include "
                f"{_format_list([_match_phrase(match) for match in required_matches])}."
            )
        if preferred_matches:
            parts.append(
                "Additional preferred skill matches include "
                f"{_format_list([_match_phrase(match) for match in preferred_matches])}."
            )
        if unclassified_matches:
            parts.append(
                "Other matched skills with unavailable classification include "
                f"{_format_list([_match_phrase(match) for match in unclassified_matches])}."
            )
    elif matches:
        parts.append(
            f"Matched skills include {_format_list([_match_phrase(match) for match in matches])}."
        )
    else:
        parts.append("No matched skills were recorded.")

    parts.extend(_evidence_sentences(matches))

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

    signal_note = candidate.get("signal_note")
    if signal_note == "semantic_above_keyword":
        parts.append("Semantic relevance is stronger than explicit keyword coverage.")
    elif signal_note == "keyword_above_semantic":
        parts.append(
            "Explicit keyword coverage is stronger than overall semantic similarity."
        )

    parts.append(
        f"The candidate recorded a {_format_score(candidate['final_score'])} final "
        f"score, with {_format_score(candidate['keyword_score'])} keyword matching "
        f"and {_format_score(candidate['semantic_score'])} semantic similarity."
    )
    return " ".join(parts)
