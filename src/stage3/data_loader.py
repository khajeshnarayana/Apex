"""Load and validate Stage 2 ranking output for Stage 3 consumers."""

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "candidate_id",
    "name",
    "rank",
    "final_score",
    "keyword_score",
    "semantic_score",
    "matched_required_skills",
    "matched_preferred_skills",
    "missing_required_skills",
    "evidence",
}

STRING_FIELDS = ("candidate_id", "name")
SCORE_FIELDS = ("final_score", "keyword_score", "semantic_score")
SKILL_LIST_FIELDS = (
    "matched_required_skills",
    "matched_preferred_skills",
    "missing_required_skills",
)


def load_rankings(file_path: str | Path) -> list[dict[str, Any]]:
    """Load ranking data from a JSON file, validate it, and sort it by rank."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Ranking file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Ranking path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as ranking_file:
            candidates = json.load(ranking_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in ranking file {path} "
            f"at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(candidates, list):
        raise ValueError("Ranking data must be a top-level JSON list.")
    if not candidates:
        raise ValueError("Ranking data must contain at least one candidate.")

    candidate_ids: set[str] = set()
    ranks: set[int] = set()

    for index, candidate in enumerate(candidates):
        location = f"Candidate at index {index}"

        if not isinstance(candidate, dict):
            raise ValueError(f"{location} must be a JSON object.")

        missing_fields = REQUIRED_FIELDS - candidate.keys()
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"{location} is missing required fields: {missing}.")

        for field in STRING_FIELDS:
            if not isinstance(candidate[field], str):
                raise ValueError(f"{location} field '{field}' must be a string.")

        rank = candidate["rank"]
        if isinstance(rank, bool) or not isinstance(rank, int):
            raise ValueError(f"{location} field 'rank' must be an integer.")

        for field in SCORE_FIELDS:
            value = candidate[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{location} field '{field}' must be a number.")

        for field in SKILL_LIST_FIELDS:
            skills = candidate[field]
            if not isinstance(skills, list) or not all(
                isinstance(skill, str) for skill in skills
            ):
                raise ValueError(
                    f"{location} field '{field}' must be a list of strings."
                )

        evidence = candidate["evidence"]
        if not isinstance(evidence, list) or not all(
            isinstance(item, dict) for item in evidence
        ):
            raise ValueError(
                f"{location} field 'evidence' must be a list of JSON objects."
            )

        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_ids:
            raise ValueError(f"Duplicate candidate_id found: {candidate_id}.")
        candidate_ids.add(candidate_id)

        if rank in ranks:
            raise ValueError(f"Duplicate rank found: {rank}.")
        ranks.add(rank)

    return sorted(candidates, key=lambda candidate: candidate["rank"])
