"""Normalize supported Stage 2 payloads for Stage 3 presentation."""

from typing import Any


SCORE_FIELDS = ("final_score", "keyword_score", "semantic_score")


def _valid_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_score(value: Any, field: str, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{location} field '{field}' must be a number.")
    score = float(value)
    if not 0 <= score <= 100:
        raise ValueError(f"{location} field '{field}' must be between 0 and 100.")
    return score if score <= 1 else score / 100


def _normalize_old_skill_list(
    value: Any, field: str, location: str
) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{location} field '{field}' must be a list.")

    normalized = []
    for index, skill in enumerate(value):
        if not _valid_text(skill):
            raise ValueError(
                f"{location} field '{field}' item {index} must be a non-empty string."
            )
        skill = skill.strip()
        normalized.append(
            {
                "skill": skill,
                "found_as": skill,
                "match_type": "exact",
                "found_in": None,
                "evidence": None,
                "required": None,
            }
        )
    return normalized


def _normalize_optional_text(value: Any, field: str, location: str) -> str | None:
    if value is None or value == "":
        return None
    if not _valid_text(value):
        raise ValueError(f"{location} field '{field}' must be a string or null.")
    return value.strip()


def _normalize_matched_skills(value: Any, location: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{location} field 'matched_skills' must be a list.")

    normalized = []
    for index, item in enumerate(value):
        item_location = f"{location} matched_skills item {index}"
        if not isinstance(item, dict):
            raise ValueError(f"{item_location} must be a JSON object.")
        skill = item.get("skill")
        if not _valid_text(skill):
            raise ValueError(
                f"{item_location} field 'skill' must be a non-empty string."
            )
        skill = skill.strip()

        found_as = item.get("found_as")
        if found_as is None or found_as == "":
            found_as = skill
        elif not _valid_text(found_as):
            raise ValueError(f"{item_location} field 'found_as' must be a string.")
        else:
            found_as = found_as.strip()

        match_type = item.get("match_type")
        if match_type is None or match_type == "":
            match_type = (
                "exact"
                if found_as.casefold() == skill.casefold()
                else "unspecified"
            )
        elif not _valid_text(match_type):
            raise ValueError(f"{item_location} field 'match_type' must be a string.")
        else:
            match_type = match_type.strip().lower()

        found_in = _normalize_optional_text(
            item.get("found_in"), "found_in", item_location
        )
        evidence = _normalize_optional_text(
            item.get("evidence"), "evidence", item_location
        )
        required = item.get("required")
        if required is not None and not isinstance(required, bool):
            raise ValueError(
                f"{item_location} field 'required' must be a boolean or null."
            )

        normalized.append(
            {
                "skill": skill,
                "found_as": found_as,
                "match_type": match_type,
                "found_in": found_in,
                "evidence": evidence,
                "required": required,
            }
        )
    return normalized


def _normalize_missing_skills(value: Any, location: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(
            f"{location} field 'missing_required_skills' must be a list."
        )

    normalized = []
    for index, item in enumerate(value):
        item_location = f"{location} missing_required_skills item {index}"
        if isinstance(item, str):
            if not item.strip():
                raise ValueError(f"{item_location} must not be empty.")
            normalized.append({"skill": item.strip(), "semantic_hint": False})
            continue
        if not isinstance(item, dict):
            raise ValueError(f"{item_location} must be a string or JSON object.")

        skill = item.get("skill")
        if not _valid_text(skill):
            raise ValueError(
                f"{item_location} field 'skill' must be a non-empty string."
            )
        semantic_hint = item.get("semantic_hint", False)
        if semantic_hint is None:
            semantic_hint = False
        if not isinstance(semantic_hint, bool):
            raise ValueError(
                f"{item_location} field 'semantic_hint' must be a boolean."
            )
        normalized.append(
            {"skill": skill.strip(), "semantic_hint": semantic_hint}
        )
    return normalized


def normalize_stage2_output(payload: Any) -> list[dict[str, Any]]:
    """Convert old mock or current Stage 2 output into one Stage 3 schema."""
    if isinstance(payload, list):
        raw_candidates = payload
    elif isinstance(payload, dict):
        if "ranked_candidates" not in payload:
            raise ValueError("Stage 2 output must contain a 'ranked_candidates' list.")
        raw_candidates = payload["ranked_candidates"]
    else:
        raise ValueError(
            "Ranking data must be a candidate list or a Stage 2 JSON object."
        )

    if not isinstance(raw_candidates, list):
        raise ValueError("Stage 2 field 'ranked_candidates' must be a list.")
    if not raw_candidates:
        raise ValueError("Ranking data must contain at least one candidate.")

    normalized_candidates = []
    candidate_ids = set()
    for display_rank, raw_candidate in enumerate(raw_candidates, start=1):
        location = f"Candidate at position {display_rank}"
        if not isinstance(raw_candidate, dict):
            raise ValueError(f"{location} must be a JSON object.")

        candidate_id = raw_candidate.get("candidate_id")
        if not _valid_text(candidate_id):
            raise ValueError(
                f"{location} field 'candidate_id' must be a non-empty string."
            )
        candidate_id = candidate_id.strip()
        if candidate_id in candidate_ids:
            raise ValueError(f"Duplicate candidate_id found: {candidate_id}.")
        candidate_ids.add(candidate_id)

        scores = {}
        for field in SCORE_FIELDS:
            if field not in raw_candidate:
                raise ValueError(f"{location} is missing required field '{field}'.")
            scores[field] = _normalize_score(raw_candidate[field], field, location)

        name = raw_candidate.get("name")
        display_name = name.strip() if _valid_text(name) else candidate_id

        if "matched_skills" in raw_candidate:
            matched_skills = _normalize_matched_skills(
                raw_candidate.get("matched_skills"), location
            )
        else:
            matched_skills = _normalize_old_skill_list(
                raw_candidate.get("matched_required_skills"),
                "matched_required_skills",
                location,
            )
            matched_skills.extend(
                _normalize_old_skill_list(
                    raw_candidate.get("matched_preferred_skills"),
                    "matched_preferred_skills",
                    location,
                )
            )

        normalized_candidates.append(
            {
                "candidate_id": candidate_id,
                "name": display_name,
                "rank": display_rank,
                **scores,
                "matched_skills": matched_skills,
                "missing_required_skills": _normalize_missing_skills(
                    raw_candidate.get("missing_required_skills"), location
                ),
                "signal_note": (
                    raw_candidate.get("signal_note")
                    if raw_candidate.get("signal_note")
                    in {"semantic_above_keyword", "keyword_above_semantic"}
                    else None
                ),
            }
        )

    return normalized_candidates
