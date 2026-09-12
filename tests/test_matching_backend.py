"""Focused regression checks for the existing Stage 2 backend."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from matching_engine.matching import keyword_score, rank_candidates  # noqa: E402


class MatchingBackendTests(unittest.TestCase):
    def test_keyword_contract_retains_evidence_and_required_classification(self) -> None:
        jd = {
            "full_text": "Required Python and REST API. Docker is preferred.",
            "required_skills": ["Python", "REST API"],
            "nice_to_have_skills": ["Docker"],
        }
        resume = {
            "candidate_id": "C1",
            "name": "Candidate One",
            "sections": {
                "skills": "Python",
                "experience": "Built REST APIs using Python.",
                "projects": "",
            },
            "extracted_skills": {
                "skills_section": ["Python"],
                "experience": ["REST APIs", "Python"],
                "projects": [],
            },
        }

        score, matches, missing = keyword_score(jd, resume)

        self.assertGreater(score, 0)
        self.assertEqual(missing, [])
        self.assertTrue(all(match["required"] is True for match in matches))
        self.assertTrue(any(match["evidence"] for match in matches))

    def test_ranker_uses_existing_fusion_and_descending_order(self) -> None:
        jd = {
            "full_text": "Required Python",
            "required_skills": ["Python"],
            "nice_to_have_skills": [],
        }
        resumes = [
            {
                "candidate_id": "low",
                "name": "Low",
                "sections": {"skills": "", "experience": "", "projects": ""},
                "extracted_skills": {"skills_section": [], "experience": [], "projects": []},
            },
            {
                "candidate_id": "high",
                "name": "High",
                "sections": {"skills": "Python", "experience": "", "projects": ""},
                "extracted_skills": {"skills_section": ["Python"], "experience": [], "projects": []},
            },
        ]

        with patch("matching_engine.matching.semantic_scores_batch", return_value=[0.1, 0.8]):
            ranked = rank_candidates(jd, resumes)

        self.assertEqual([candidate["candidate_id"] for candidate in ranked], ["high", "low"])


if __name__ == "__main__":
    unittest.main()
