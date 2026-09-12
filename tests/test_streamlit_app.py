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

    def test_result_pages_are_empty_before_analysis(self) -> None:
        for page in (
            "Leading Candidates",
            "Rankings",
            "Candidate Details",
            "Candidate Comparison",
        ):
            self.app.radio[0].set_value(page)
            self.app.run(timeout=20)
            markup = " ".join(
                markdown.value for markdown in self.app.markdown
            )
            self.assertEqual(len(self.app.exception), 0)
            self.assertIn("No analysis available yet", markup)
            self.assertNotIn("Aisha Mehta", markup)
            self.assertNotIn("Rohan Das", markup)
            self.assertTrue(
                any(button.label == "Go to Upload Documents" for button in self.app.button)
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

        self.app.radio[0].set_value("Leading Candidates")
        self.app.run(timeout=20)
        reset_markup = " ".join(
            markdown.value for markdown in self.app.markdown
        )
        self.assertIn("No analysis available yet", reset_markup)
        self.assertNotIn("Aisha Mehta", reset_markup)


class ContrastStyleTests(unittest.TestCase):
    @staticmethod
    def _relative_luminance(hex_color: str) -> float:
        channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    def _contrast_ratio(self, first: str, second: str) -> float:
        first_luminance = self._relative_luminance(first)
        second_luminance = self._relative_luminance(second)
        lighter = max(first_luminance, second_luminance)
        darker = min(first_luminance, second_luminance)
        return (lighter + 0.05) / (darker + 0.05)

    def test_sidebar_and_uploader_pairs_meet_normal_text_contrast(self) -> None:
        self.assertGreaterEqual(self._contrast_ratio("#ebe6dc", "#4d514c"), 4.5)
        self.assertGreaterEqual(self._contrast_ratio("#ebe6dc", "#1c211e"), 4.5)
        self.assertGreaterEqual(self._contrast_ratio("#fbfaf6", "#4d514c"), 4.5)
        self.assertGreaterEqual(self._contrast_ratio("#1c211e", "#fbfaf6"), 4.5)

    def test_styles_cover_nested_streamlit_text_icons_and_states(self) -> None:
        stylesheet = (REPOSITORY_ROOT / "app" / "styles.py").read_text(
            encoding="utf-8"
        )
        for selector in (
            '[data-testid="stSidebar"] [data-testid="stRadio"] label p',
            '[data-testid="stSidebar"] [data-testid="stRadio"] label svg',
            '[data-testid="stSidebar"] [data-testid="stRadioOption"]',
            '[data-testid="stFileUploaderDropzoneInstructions"]',
            '[data-testid="stFileUploaderDropzone"] button *',
            '[data-testid="stFileUploaderDropzone"] button:hover',
            '[data-testid="stFileUploaderDropzone"] button:focus-visible',
        ):
            self.assertIn(selector, stylesheet)


if __name__ == "__main__":
    unittest.main()
