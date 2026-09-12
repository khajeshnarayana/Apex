"""Streamlit AppTest coverage for upload navigation and persisted analysis."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = REPOSITORY_ROOT / "src"
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

from stage3 import load_rankings  # noqa: E402


class StreamlitUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = AppTest.from_file(
            str(REPOSITORY_ROOT / "app" / "streamlit_app.py")
        ).run(timeout=20)

    def test_upload_page_is_default_and_missing_files_fail_cleanly(self) -> None:
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.get("file_uploader")), 2)
        self.assertEqual(self.app.radio[0].value, "Upload Documents")
        upload_markup = " ".join(markdown.value for markdown in self.app.markdown)
        self.assertIn("required", upload_markup.lower())
        self.assertIn("nice-to-have", upload_markup.lower())
        self.assertIn("PDF, DOCX, TXT, XML", upload_markup)

        self.app.button[0].click().run(timeout=20)

        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(
            any("job description" in error.value.lower() for error in self.app.error)
        )

    def test_results_persist_across_pages_and_reset(self) -> None:
        candidates = load_rankings(
            REPOSITORY_ROOT / "demo_data" / "mock_ranking_results.json"
        )
        original_candidates = copy.deepcopy(candidates)
        self.app.session_state["analysis_candidates"] = candidates
        self.app.session_state["analysis_files"] = {
            "job_description": "job.txt",
            "resumes": ["one.txt", "two.txt", "three.txt"],
        }

        self.app.radio[0].set_value("Leading Candidates")
        self.app.run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.get("column")), 0)
        leading_markup = " ".join(markdown.value for markdown in self.app.markdown)
        candidate_positions = [
            leading_markup.index(candidate["name"]) for candidate in candidates[:3]
        ]
        self.assertEqual(candidate_positions, sorted(candidate_positions))

        self.app.radio[0].set_value("Candidate Details")
        self.app.run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.selectbox), 1)
        for candidate in candidates:
            self.app.selectbox[0].set_value(candidate["candidate_id"])
            self.app.run(timeout=20)
            self.assertEqual(len(self.app.exception), 0)
            detail_markup = " ".join(
                markdown.value for markdown in self.app.markdown
            )
            self.assertIn(candidate["name"], detail_markup)

        self.app.radio[0].set_value("Candidate Comparison")
        self.app.run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.selectbox), 2)
        comparison_markup = " ".join(
            markdown.value for markdown in self.app.markdown
        )
        self.assertIn("Shared matched skills", comparison_markup)

        first_id = candidates[0]["candidate_id"]
        self.app.selectbox[0].set_value(first_id)
        self.app.selectbox[1].set_value(first_id)
        self.app.run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(
            any("two different candidates" in info.value.lower() for info in self.app.info)
        )
        self.assertEqual(self.app.session_state["analysis_candidates"], original_candidates)

        reset = next(
            button
            for button in self.app.button
            if button.label.startswith("Clear analysis")
        )
        reset.click().run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertNotIn("analysis_candidates", self.app.session_state)
        self.assertEqual(self.app.radio[0].value, "Upload Documents")


if __name__ == "__main__":
    unittest.main()
