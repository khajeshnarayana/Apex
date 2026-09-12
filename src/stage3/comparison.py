"""Compare normalized candidates without recalculating Stage 2 rankings."""

from typing import Any


def _candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "name": candidate["name"],
        "rank": candidate["rank"],
        "final_score": candidate["final_score"],
        "keyword_score": candidate["keyword_score"],
        "semantic_score": candidate["semantic_score"],
    }


def _unique_skill_names(
    primary: list[dict[str, str]], other: list[dict[str, str]]
) -> list[str]:
    other_skills = {match["skill"] for match in other}
    return list(
        dict.fromkeys(
            match["skill"]
            for match in primary
            if match["skill"] not in other_skills
        )
    )


def _format_skills(skills: list[str]) -> str:
    if len(skills) == 1:
        return skills[0]
    if len(skills) == 2:
        return f"{skills[0]} and {skills[1]}"
    return f"{', '.join(skills[:-1])}, and {skills[-1]}"


def _percentage_points(difference: float) -> str:
    return f"{difference * 100:.1f}"


def compare_candidates(
    candidate_a: dict[str, Any], candidate_b: dict[str, Any]
) -> dict[str, Any]:
    """Compare normalized records using their authoritative display ranks."""
    if candidate_a["candidate_id"] == candidate_b["candidate_id"]:
        raise ValueError("Two different candidates are required for comparison.")
    if candidate_a["rank"] == candidate_b["rank"]:
        raise ValueError("Candidates must have different display ranks.")

    if candidate_a["rank"] < candidate_b["rank"]:
        higher_ranked = candidate_a
        lower_ranked = candidate_b
    else:
        higher_ranked = candidate_b
        lower_ranked = candidate_a

    return {
        "candidate_a": _candidate_summary(candidate_a),
        "candidate_b": _candidate_summary(candidate_b),
        "higher_ranked_candidate": _candidate_summary(higher_ranked),
        "lower_ranked_candidate": _candidate_summary(lower_ranked),
        "rank_difference": abs(candidate_a["rank"] - candidate_b["rank"]),
        "final_score_difference": round(
            abs(candidate_a["final_score"] - candidate_b["final_score"]), 10
        ),
        "keyword_score_difference": round(
            abs(candidate_a["keyword_score"] - candidate_b["keyword_score"]),
            10,
        ),
        "semantic_score_difference": round(
            abs(candidate_a["semantic_score"] - candidate_b["semantic_score"]),
            10,
        ),
        "candidate_a_unique_matched_skills": _unique_skill_names(
            candidate_a["matched_skills"], candidate_b["matched_skills"]
        ),
        "candidate_b_unique_matched_skills": _unique_skill_names(
            candidate_b["matched_skills"], candidate_a["matched_skills"]
        ),
        "candidate_a_missing_required_skills": [
            dict(item) for item in candidate_a["missing_required_skills"]
        ],
        "candidate_b_missing_required_skills": [
            dict(item) for item in candidate_b["missing_required_skills"]
        ],
    }


def generate_comparison_explanation(comparison: dict[str, Any]) -> str:
    """Explain only facts already present in a normalized comparison result."""
    candidate_a = comparison["candidate_a"]
    higher = comparison["higher_ranked_candidate"]
    lower = comparison["lower_ranked_candidate"]
    rank_difference = comparison["rank_difference"]
    position_label = "position" if rank_difference == 1 else "positions"
    parts = [
        f"{higher['name']} ranks above {lower['name']} by "
        f"{rank_difference} {position_label}."
    ]

    final_difference = comparison["final_score_difference"]
    if higher["final_score"] > lower["final_score"]:
        parts.append(
            f"{higher['name']} also has a {_percentage_points(final_difference)} "
            "percentage-point higher final score."
        )
    elif higher["final_score"] < lower["final_score"]:
        parts.append(
            f"{lower['name']} has a {_percentage_points(final_difference)} "
            f"percentage-point higher final score despite {higher['name']}'s "
            "higher recorded rank."
        )
    else:
        parts.append("Their recorded final scores are equal.")

    higher_is_a = higher["candidate_id"] == candidate_a["candidate_id"]
    higher_side, lower_side = ("a", "b") if higher_is_a else ("b", "a")
    higher_unique = comparison[f"candidate_{higher_side}_unique_matched_skills"]
    lower_unique = comparison[f"candidate_{lower_side}_unique_matched_skills"]
    higher_missing = comparison[
        f"candidate_{higher_side}_missing_required_skills"
    ]
    lower_missing = comparison[f"candidate_{lower_side}_missing_required_skills"]

    if higher_unique:
        label = "skill" if len(higher_unique) == 1 else "skills"
        parts.append(
            f"{higher['name']} uniquely matched {label} "
            f"{_format_skills(higher_unique)}."
        )
    if lower_unique:
        label = "skill" if len(lower_unique) == 1 else "skills"
        parts.append(
            f"{lower['name']} uniquely matched {label} "
            f"{_format_skills(lower_unique)}."
        )

    parts.append(
        f"{higher['name']} has {len(higher_missing)} missing required "
        f"skill{'s' if len(higher_missing) != 1 else ''}, compared with "
        f"{len(lower_missing)} for {lower['name']}."
    )

    keyword_difference = comparison["keyword_score_difference"]
    semantic_difference = comparison["semantic_score_difference"]
    if keyword_difference or semantic_difference:
        parts.append(
            "The absolute keyword and semantic score differences are "
            f"{_percentage_points(keyword_difference)} and "
            f"{_percentage_points(semantic_difference)} percentage points, "
            "respectively."
        )
    return " ".join(parts)
