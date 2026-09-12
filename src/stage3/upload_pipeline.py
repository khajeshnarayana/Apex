"""Local upload orchestration from Stage 1 extraction to Stage 3 records."""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .stage2_adapter import normalize_stage2_output


SUPPORTED_EXTENSIONS = ("pdf", "docx", "txt", "xml")
_SUPPORTED_SUFFIXES = {f".{extension}" for extension in SUPPORTED_EXTENSIONS}
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


def build_job_description(
    clean_text: str,
    jd_parser: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build Stage 2 JD input through the authoritative backend parser."""
    if not isinstance(clean_text, str) or not clean_text.strip():
        raise UploadPipelineError("The job description contains no extractable text.")

    if jd_parser is None:
        try:
            from matching_engine.jd_config import parse_jd
        except (ImportError, OSError) as error:
            raise UploadPipelineError(
                f"The local job-description parser is unavailable: {error}"
            ) from error
        jd_parser = parse_jd

    jd_data = jd_parser(clean_text.strip())
    if not isinstance(jd_data, dict):
        raise UploadPipelineError("The job-description parser returned malformed data.")
    if not jd_data.get("required_skills"):
        raise UploadPipelineError(
            "No required skills could be identified in the job description."
        )
    return jd_data


def analyze_documents(
    job_description: UploadedDocument | None,
    resumes: Sequence[UploadedDocument],
    *,
    text_extractor: Callable[[str], Any] | None = None,
    resume_builder: Callable[[str, str], dict[str, Any]] | None = None,
    resume_adapter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    jd_parser: Callable[[str], dict[str, Any]] | None = None,
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
            jd_parser,
            ranker,
        )
    ):
        try:
            from hidden_text_strip import build_resume_json, extract_clean_text
            from matching_engine.adapter import adapt
            from matching_engine.jd_config import parse_jd
            from matching_engine.matching import rank_candidates
        except (ImportError, OSError) as error:
            raise UploadPipelineError(
                f"The local document-analysis backend is unavailable: {error}"
            ) from error

        text_extractor = text_extractor or extract_clean_text
        resume_builder = resume_builder or build_resume_json
        resume_adapter = resume_adapter or adapt
        jd_parser = jd_parser or parse_jd
        ranker = ranker or rank_candidates

    assert text_extractor is not None
    assert resume_builder is not None
    assert resume_adapter is not None
    assert jd_parser is not None
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
                jd_parser=jd_parser,
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
