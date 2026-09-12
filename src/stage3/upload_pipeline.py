"""Local upload orchestration from Stage 1 extraction to Stage 3 records."""

from __future__ import annotations

import re
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .stage2_adapter import normalize_stage2_output


SUPPORTED_EXTENSIONS = ("pdf", "docx", "txt", "xml")
_SUPPORTED_SUFFIXES = {f".{extension}" for extension in SUPPORTED_EXTENSIONS}
_REQUIRED_MARKERS = (
    "required skills",
    "requirements",
    "required",
    "must have",
    "must-have",
    "mandatory",
    "essential",
)
_PREFERRED_MARKERS = (
    "nice to have",
    "nice-to-have",
    "preferred skills",
    "preferred",
    "desirable",
    "bonus",
    "a plus",
)


class UploadPipelineError(ValueError):
    """A safe, user-facing failure in document analysis."""


@dataclass(frozen=True)
class UploadedDocument:
    """Framework-independent uploaded file value."""

    name: str
    content: bytes


def from_streamlit_upload(upload: Any) -> UploadedDocument:
    """Copy one Streamlit UploadedFile into a framework-independent value."""
    return UploadedDocument(name=str(upload.name), content=bytes(upload.getvalue()))


def _validated_name(document: UploadedDocument, role: str) -> str:
    name = document.name.strip()
    if not name or Path(name).name != name:
        raise UploadPipelineError(f"{role} has an invalid filename.")
    suffix = Path(name).suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        supported = ", ".join(extension.upper() for extension in SUPPORTED_EXTENSIONS)
        raise UploadPipelineError(
            f"Unsupported file type for {name}. Supported types: {supported}."
        )
    if not document.content:
        raise UploadPipelineError(f"{name} is empty.")
    return name


def validate_uploads(
    job_description: UploadedDocument | None,
    resumes: Sequence[UploadedDocument],
) -> tuple[str, list[str]]:
    """Validate upload presence, types, content, and filename uniqueness."""
    if job_description is None:
        raise UploadPipelineError("Upload one job description before analysis.")
    if not resumes:
        raise UploadPipelineError("Upload at least one candidate resume before analysis.")

    jd_name = _validated_name(job_description, "Job description")
    resume_names = [
        _validated_name(document, "Candidate resume") for document in resumes
    ]
    all_names = [jd_name, *resume_names]
    folded_names = [name.casefold() for name in all_names]
    duplicates = sorted(
        {name for name in folded_names if folded_names.count(name) > 1}
    )
    if duplicates:
        raise UploadPipelineError(
            "Duplicate filenames are not allowed: " + ", ".join(duplicates) + "."
        )
    return jd_name, resume_names


def _marker_kind(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.casefold()).strip(" :-–—\t")
    if any(marker in normalized for marker in _PREFERRED_MARKERS):
        return "preferred"
    if any(marker in normalized for marker in _REQUIRED_MARKERS):
        return "required"
    return None


def _classified_job_text(clean_text: str) -> tuple[str, str]:
    required_chunks: list[str] = []
    preferred_chunks: list[str] = []
    active_section: str | None = None

    for raw_line in clean_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        statements = re.split(r"(?<=[.!?])\s+", line)
        for statement in statements:
            kind = _marker_kind(statement)
            if kind is not None:
                active_section = kind
            elif statement.endswith(":") and len(statement) <= 80:
                active_section = None
                continue

            target = kind or active_section
            if target == "required":
                required_chunks.append(statement)
            elif target == "preferred":
                preferred_chunks.append(statement)

    return "\n".join(required_chunks), "\n".join(preferred_chunks)


def build_job_description(
    clean_text: str,
    skill_extractor: Callable[[str], list[str]],
) -> dict[str, Any]:
    """Build Stage 2 JD input from explicitly classified JD language."""
    if not isinstance(clean_text, str) or not clean_text.strip():
        raise UploadPipelineError("The job description contains no extractable text.")

    required_text, preferred_text = _classified_job_text(clean_text)
    required_skills = (
        list(dict.fromkeys(skill_extractor(required_text)))
        if required_text
        else []
    )
    preferred_skills = [
        skill
        for skill in (
            list(dict.fromkeys(skill_extractor(preferred_text)))
            if preferred_text
            else []
        )
        if skill not in required_skills
    ]
    if not required_skills:
        raise UploadPipelineError(
            "No explicitly labelled required skills were found in the job description. "
            "Use wording such as 'Required skills' or 'Must have'."
        )
    return {
        "full_text": clean_text.strip(),
        "required_skills": required_skills,
        "nice_to_have_skills": preferred_skills,
    }


def analyze_documents(
    job_description: UploadedDocument | None,
    resumes: Sequence[UploadedDocument],
    *,
    text_extractor: Callable[[str], Any] | None = None,
    resume_builder: Callable[[str, str], dict[str, Any]] | None = None,
    resume_adapter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    skill_extractor: Callable[[str], list[str]] | None = None,
    ranker: Callable[[dict[str, Any], list[dict[str, Any]]], Any] | None = None,
) -> list[dict[str, Any]]:
    """Run uploaded files through the existing extraction and ranking backend."""
    jd_name, resume_names = validate_uploads(job_description, resumes)
    assert job_description is not None

    if any(
        dependency is None
        for dependency in (
            text_extractor,
            resume_builder,
            resume_adapter,
            skill_extractor,
            ranker,
        )
    ):
        try:
            from hidden_text_strip import build_resume_json, extract_clean_text
            from matching_engine.adapter import adapt, extract_skills_from_text
            from matching_engine.matching import rank_candidates
        except (ImportError, OSError) as error:
            raise UploadPipelineError(
                f"The local document-analysis backend is unavailable: {error}"
            ) from error

        text_extractor = text_extractor or extract_clean_text
        resume_builder = resume_builder or build_resume_json
        resume_adapter = resume_adapter or adapt
        skill_extractor = skill_extractor or extract_skills_from_text
        ranker = ranker or rank_candidates

    assert text_extractor is not None
    assert resume_builder is not None
    assert resume_adapter is not None
    assert skill_extractor is not None
    assert ranker is not None

    with tempfile.TemporaryDirectory(prefix="apex_upload_") as temporary_directory:
        temporary_root = Path(temporary_directory)
        jd_path = temporary_root / "job_description" / jd_name
        resumes_root = temporary_root / "resumes"
        jd_path.parent.mkdir()
        resumes_root.mkdir()
        jd_path.write_bytes(job_description.content)

        try:
            extracted_jd = text_extractor(str(jd_path))
            jd_text = getattr(extracted_jd, "clean_text", extracted_jd)
            jd_data = build_job_description(
                jd_text,
                skill_extractor=skill_extractor,
            )
        except UploadPipelineError:
            raise
        except Exception as error:
            raise UploadPipelineError(
                f"Could not extract the job description {jd_name}: {error}"
            ) from error

        adapted_resumes: list[dict[str, Any]] = []
        for index, (document, name) in enumerate(zip(resumes, resume_names), start=1):
            path = resumes_root / name
            path.write_bytes(document.content)
            try:
                parsed_resume = resume_builder(str(path), f"resume_{index:03d}")
                if not str(parsed_resume.get("full_text_clean", "")).strip():
                    raise UploadPipelineError(f"{name} contains no extractable text.")
                adapted_resumes.append(resume_adapter(parsed_resume))
            except UploadPipelineError:
                raise
            except Exception as error:
                raise UploadPipelineError(
                    f"Could not extract candidate resume {name}: {error}"
                ) from error

        try:
            ranked = ranker(jd_data, adapted_resumes)
        except Exception as error:
            raise UploadPipelineError(f"Stage 2 ranking failed: {error}") from error

        try:
            return normalize_stage2_output(ranked)
        except (TypeError, ValueError) as error:
            raise UploadPipelineError(f"Stage 2 returned malformed output: {error}") from error


def reset_analysis_state(state: Any) -> None:
    """Clear analyzed results and invalidate upload widgets for a fresh dataset."""
    for key in ("analysis_candidates", "analysis_files", "candidate_a", "candidate_b"):
        state.pop(key, None)
    state["upload_generation"] = int(state.get("upload_generation", 0)) + 1
    state["navigation"] = "Upload Documents"
