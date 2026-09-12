"""Regression tests for the local document-upload integration."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = REPOSITORY_ROOT / "src"
for import_path in (REPOSITORY_ROOT, SOURCE_DIRECTORY):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from stage3 import (  # noqa: E402
    UploadPipelineError,
    UploadedDocument,
    analyze_documents,
    build_job_description,
    compare_candidates,
    reset_analysis_state,
    validate_uploads,
)


JD = UploadedDocument(
    "job.txt",
    b"""Backend Developer
Required skills:
Python, REST API, SQL
Nice to have:
Docker and AWS
""",
)
RESUME_A = UploadedDocument(
    "alex.txt",
    b"""Alex Alpha
Skills
Python, SQL, Git
Experience
Built REST APIs using Python and PostgreSQL.
Projects
Containerized a service with Docker.
""",
)
RESUME_B = UploadedDocument(
    "blair.txt",
    b"""Blair Beta
Skills
Python, AWS
Experience
Developed Python automation tools.
Projects
Deployed a web service to AWS.
""",
)


class UploadValidationTests(unittest.TestCase):
    def test_missing_job_description_and_resumes_fail_safely(self) -> None:
        with self.assertRaisesRegex(UploadPipelineError, "job description"):
            validate_uploads(None, [RESUME_A])
        with self.assertRaisesRegex(UploadPipelineError, "at least one"):
            validate_uploads(JD, [])

    def test_one_resume_is_supported(self) -> None:
        self.assertEqual(validate_uploads(JD, [RESUME_A]), ("job.txt", ["alex.txt"]))

    def test_unsupported_empty_and_duplicate_files_fail_safely(self) -> None:
        with self.assertRaisesRegex(UploadPipelineError, "Unsupported file type"):
            validate_uploads(JD, [UploadedDocument("resume.csv", b"data")])
        with self.assertRaisesRegex(UploadPipelineError, "is empty"):
            validate_uploads(JD, [UploadedDocument("resume.txt", b"")])
        with self.assertRaisesRegex(UploadPipelineError, "Duplicate filenames"):
            validate_uploads(JD, [UploadedDocument("JOB.TXT", b"resume")])


class JobDescriptionAdapterTests(unittest.TestCase):
    def test_only_explicit_required_and_preferred_language_is_classified(self) -> None:
        vocabulary = ["Python", "REST API", "SQL", "Docker", "AWS", "React"]

        def extract(text: str) -> list[str]:
            return [skill for skill in vocabulary if skill.casefold() in text.casefold()]

        result = build_job_description(
            "Role uses React.\nRequired: Python, REST API and SQL.\nAWS is a plus.",
            extract,
        )

        self.assertEqual(result["required_skills"], ["Python", "REST API", "SQL"])
        self.assertEqual(result["nice_to_have_skills"], ["AWS"])
        self.assertNotIn("React", result["required_skills"])

    def test_unclassified_job_description_does_not_fabricate_requirements(self) -> None:
        with self.assertRaisesRegex(UploadPipelineError, "explicitly labelled"):
            build_job_description("Python role", lambda text: ["Python"])


class UploadPipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from hidden_text_strip import build_resume_json, extract_clean_text
        from matching_engine.adapter import adapt, extract_skills_from_text

        cls.text_extractor = staticmethod(extract_clean_text)
        cls.resume_builder = staticmethod(build_resume_json)
        cls.resume_adapter = staticmethod(adapt)
        cls.skill_extractor = staticmethod(extract_skills_from_text)

    def _analyze(self, resumes, ranker):
        return analyze_documents(
            JD,
            resumes,
            text_extractor=self.text_extractor,
            resume_builder=self.resume_builder,
            resume_adapter=self.resume_adapter,
            skill_extractor=self.skill_extractor,
            ranker=ranker,
        )

    def test_real_ingestion_and_adapter_feed_multiple_resumes_to_stage2(self) -> None:
        observed = {}

        def backend_ranker(jd_data, resumes):
            observed["jd"] = jd_data
            observed["resumes"] = resumes
            return [
                {
                    "candidate_id": resumes[1]["candidate_id"],
                    "name": resumes[1]["name"],
                    "final_score": 0.81,
                    "keyword_score": 0.72,
                    "semantic_score": 0.87,
                    "matched_skills": [],
                    "missing_required_skills": [],
                },
                {
                    "candidate_id": resumes[0]["candidate_id"],
                    "name": resumes[0]["name"],
                    "final_score": 0.69,
                    "keyword_score": 0.65,
                    "semantic_score": 0.72,
                    "matched_skills": [],
                    "missing_required_skills": [],
                },
            ]

        candidates = self._analyze([RESUME_A, RESUME_B], backend_ranker)

        self.assertEqual(observed["jd"]["required_skills"], ["REST API", "Python", "SQL"])
        self.assertEqual(observed["jd"]["nice_to_have_skills"], ["Docker", "AWS"])
        self.assertEqual([resume["name"] for resume in observed["resumes"]], ["Alex Alpha", "Blair Beta"])
        self.assertEqual([candidate["name"] for candidate in candidates], ["Blair Beta", "Alex Alpha"])
        self.assertEqual([candidate["rank"] for candidate in candidates], [1, 2])
        self.assertEqual([candidate["final_score"] for candidate in candidates], [0.81, 0.69])

        selected = {candidate["candidate_id"]: candidate for candidate in candidates}
        self.assertEqual(selected["resume_002"]["name"], "Blair Beta")
        comparison = compare_candidates(candidates[0], candidates[1])
        self.assertEqual(comparison["higher_ranked_candidate"]["candidate_id"], "resume_002")

    def test_stage2_failures_and_malformed_output_are_wrapped(self) -> None:
        def failed_ranker(_jd, _resumes):
            raise RuntimeError("backend unavailable")

        with self.assertRaisesRegex(UploadPipelineError, "Stage 2 ranking failed"):
            self._analyze([RESUME_A], failed_ranker)
        with self.assertRaisesRegex(UploadPipelineError, "malformed output"):
            self._analyze([RESUME_A], lambda _jd, _resumes: {"wrong": []})

    def test_empty_extraction_and_parser_failure_are_wrapped(self) -> None:
        empty_resume = UploadedDocument("empty.txt", b"   \n")
        with self.assertRaisesRegex(UploadPipelineError, "no extractable text"):
            self._analyze([empty_resume], lambda _jd, _resumes: [])

        def broken_builder(_path, _resume_id):
            raise RuntimeError("parser broke")

        with self.assertRaisesRegex(UploadPipelineError, "parser broke"):
            analyze_documents(
                JD,
                [RESUME_A],
                text_extractor=self.text_extractor,
                resume_builder=broken_builder,
                resume_adapter=self.resume_adapter,
                skill_extractor=self.skill_extractor,
                ranker=lambda _jd, _resumes: [],
            )


class StateAndOfflineTests(unittest.TestCase):
    def test_reset_clears_results_and_invalidates_upload_widgets(self) -> None:
        state = {
            "analysis_candidates": [{"candidate_id": "C1"}],
            "analysis_files": {"job_description": "job.txt"},
            "upload_generation": 4,
            "navigation": "Candidate Details",
            "candidate_a": "C1",
            "candidate_b": "C2",
        }

        reset_analysis_state(state)

        self.assertNotIn("analysis_candidates", state)
        self.assertNotIn("analysis_files", state)
        self.assertNotIn("candidate_a", state)
        self.assertNotIn("candidate_b", state)
        self.assertEqual(state["upload_generation"], 5)
        self.assertEqual(state["navigation"], "Upload Documents")

    def test_embedding_model_is_loaded_without_network_access(self) -> None:
        import matching_engine.matching as matching

        matching._model = None
        sentinel = object()
        with patch.object(matching, "SentenceTransformer", return_value=sentinel) as loader:
            self.assertIs(matching.get_model(), sentinel)
        loader.assert_called_once_with("all-MiniLM-L6-v2", local_files_only=True)
        matching._model = None


if __name__ == "__main__":
    unittest.main()
