"""Streamlit AppTest coverage for upload navigation and persisted analysis."""

from __future__ import annotations

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

        self.app.button[0].click().run(timeout=20)

        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(
            any("job description" in error.value.lower() for error in self.app.error)
        )

    def test_results_persist_across_pages_and_reset(self) -> None:
        candidates = load_rankings(
            REPOSITORY_ROOT / "demo_data" / "mock_ranking_results.json"
        )
        self.app.session_state["analysis_candidates"] = candidates
        self.app.session_state["analysis_files"] = {
            "job_description": "job.txt",
            "resumes": ["one.txt", "two.txt", "three.txt"],
        }

        self.app.radio[0].set_value("Candidate Details")
        self.app.run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.selectbox), 1)

        self.app.radio[0].set_value("Candidate Comparison")
        self.app.run(timeout=20)
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.selectbox), 2)

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
