"""Generate deterministic explanations from structured Stage 2 output."""

from typing import Any


def _format_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def generate_explanation(candidate: dict[str, Any]) -> str:
    """Build an evidence-grounded explanation from Stage 2 candidate fields."""
    explanation_parts: list[str] = []

    matched_required_skills = candidate["matched_required_skills"]
    if matched_required_skills:
        if len(matched_required_skills) == 1:
            explanation_parts.append(
                f"Matched required skill: {matched_required_skills[0]}."
            )
        else:
            explanation_parts.append(
                "Matched required skills include "
                f"{_format_list(matched_required_skills)}."
            )

    matched_preferred_skills = candidate["matched_preferred_skills"]
    if matched_preferred_skills:
        if len(matched_preferred_skills) == 1:
            explanation_parts.append(
                "Also matched the preferred skill "
                f"{matched_preferred_skills[0]}."
            )
        else:
            explanation_parts.append(
                "Also matched preferred skills such as "
                f"{_format_list(matched_preferred_skills)}."
            )

    evidence = candidate["evidence"]
    if evidence:
        resume_evidence = evidence[0].get("resume_evidence")
        if isinstance(resume_evidence, str) and resume_evidence.strip():
            evidence_text = resume_evidence.strip()
            if evidence_text[-1] not in ".!?":
                evidence_text += "."
            explanation_parts.append(
                f"Supporting evidence includes: {evidence_text}"
            )

    missing_required_skills = candidate["missing_required_skills"]
    if missing_required_skills:
        skill_label = "skill" if len(missing_required_skills) == 1 else "skills"
        explanation_parts.append(
            f"Missing or unverified required {skill_label}: "
            f"{_format_list(missing_required_skills)}."
        )
    else:
        explanation_parts.append("No required skills were identified as missing.")

    explanation_parts.append(
        f"Recorded scores: {candidate['final_score']:.1f} final, "
        f"{candidate['keyword_score']:.1f} keyword, and "
        f"{candidate['semantic_score']:.1f} semantic."
    )

    return " ".join(explanation_parts)
