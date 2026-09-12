"""Focused regression tests for the extended Stage 2 to Stage 3 contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SOURCE_DIRECTORY = Path(__file__).resolve().parents[1] / "src"
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

from stage3 import (  # noqa: E402
    compare_candidates,
    generate_comparison_explanation,
    generate_explanation,
    load_rankings,
    normalize_stage2_output,
)


def current_payload() -> dict:
    return {
        "ranked_candidates": [
            {
                "candidate_id": "C-A",
                "name": "Candidate A",
                "final_score": 0.52,
                "keyword_score": 0.44,
                "semantic_score": 0.60,
                "signal_note": "semantic_above_keyword",
                "matched_skills": [
                    {
                        "skill": "REST API",
                        "found_as": "REST APIs",
                        "match_type": "synonym",
                        "found_in": "Experience",
                        "evidence": "Built REST APIs for mobile applications.",
                        "required": True,
                    },
                    {
                        "skill": "SQL",
                        "found_as": "SQL",
                        "match_type": "exact",
                        "found_in": None,
                        "evidence": None,
                        "required": True,
                    },
                    {
                        "skill": "Git",
                        "found_as": "GitHub",
                        "match_type": "synonym",
                        "found_in": "Projects",
                        "evidence": "Maintained project history in GitHub.",
                        "required": False,
                    },
                    {
                        "skill": "Testing",
                        "found_as": "unit tests",
                        "match_type": "synonym",
                        "found_in": None,
                        "evidence": "Added unit tests for service endpoints.",
                    },
                ],
                "missing_required_skills": [
                    {"skill": "Docker", "semantic_hint": True}
                ],
            },
            {
                "candidate_id": "C-B",
                "name": "Candidate B",
                "final_score": 0.74,
                "keyword_score": 0.78,
                "semantic_score": 0.70,
                "signal_note": "keyword_above_semantic",
                "matched_skills": [
                    {
                        "skill": "REST API",
                        "found_as": "REST API",
                        "match_type": "exact",
                        "required": True,
                    },
                    {
                        "skill": "NoSQL",
                        "found_as": "MongoDB",
                        "match_type": "synonym",
                        "required": False,
                    },
                ],
                "missing_required_skills": [],
            },
        ]
    }


class AdapterExtensionTests(unittest.TestCase):
    def test_preserves_new_match_metadata_and_signal_notes(self) -> None:
        candidates = normalize_stage2_output(current_payload())
        first_match = candidates[0]["matched_skills"][0]

        self.assertEqual(first_match["found_in"], "Experience")
        self.assertEqual(
            first_match["evidence"], "Built REST APIs for mobile applications."
        )
        self.assertIs(first_match["required"], True)
        self.assertIs(candidates[0]["matched_skills"][2]["required"], False)
        self.assertIsNone(candidates[0]["matched_skills"][3]["required"])
        self.assertIsNone(candidates[0]["matched_skills"][1]["found_in"])
        self.assertIsNone(candidates[0]["matched_skills"][1]["evidence"])
        self.assertEqual(candidates[0]["signal_note"], "semantic_above_keyword")
        self.assertEqual(candidates[1]["signal_note"], "keyword_above_semantic")

    def test_current_contract_also_accepts_top_level_list(self) -> None:
        payload = current_payload()

        wrapped = normalize_stage2_output(payload)
        listed = normalize_stage2_output(payload["ranked_candidates"])

        self.assertEqual(listed, wrapped)

    def test_unknown_and_null_signal_notes_degrade_to_none(self) -> None:
        payload = current_payload()
        payload["ranked_candidates"][0]["signal_note"] = "future_signal"
        payload["ranked_candidates"][1]["signal_note"] = None

        candidates = normalize_stage2_output(payload)

        self.assertIsNone(candidates[0]["signal_note"])
        self.assertIsNone(candidates[1]["signal_note"])

    def test_old_list_contract_gets_null_metadata_without_inference(self) -> None:
        candidates = normalize_stage2_output(
            [
                {
                    "candidate_id": "OLD-1",
                    "name": "Legacy Candidate",
                    "final_score": 92.4,
                    "keyword_score": 90.0,
                    "semantic_score": 94.8,
                    "matched_required_skills": ["React"],
                    "matched_preferred_skills": ["Git"],
                    "missing_required_skills": [],
                }
            ]
        )

        self.assertEqual(candidates[0]["rank"], 1)
        self.assertEqual(candidates[0]["final_score"], 0.924)
        for match in candidates[0]["matched_skills"]:
            self.assertEqual(match["match_type"], "exact")
            self.assertIsNone(match["found_in"])
            self.assertIsNone(match["evidence"])
            self.assertIsNone(match["required"])
        self.assertIsNone(candidates[0]["signal_note"])

    def test_repository_mock_still_loads(self) -> None:
        mock_path = Path(__file__).resolve().parents[1] / "demo_data" / "mock_ranking_results.json"
        candidates = load_rankings(mock_path)

        self.assertEqual(len(candidates), 3)
        self.assertEqual([candidate["rank"] for candidate in candidates], [1, 2, 3])
        self.assertTrue(
            all(
                match["required"] is None
                for candidate in candidates
                for match in candidate["matched_skills"]
            )
        )

    def test_invalid_optional_metadata_is_rejected_clearly(self) -> None:
        payload = current_payload()
        payload["ranked_candidates"][0]["matched_skills"][0]["required"] = "yes"
        with self.assertRaisesRegex(ValueError, "boolean or null"):
            normalize_stage2_output(payload)


class ExplanationExtensionTests(unittest.TestCase):
    def test_explanation_is_deterministic_grouped_and_evidence_limited(self) -> None:
        candidate = normalize_stage2_output(current_payload())[0]

        first = generate_explanation(candidate)
        second = generate_explanation(candidate)

        self.assertEqual(first, second)
        self.assertIn("Matched required skills include REST API via REST APIs and SQL.", first)
        self.assertIn("Additional preferred skill matches include Git via GitHub.", first)
        self.assertIn("classification include Testing via unit tests", first)
        self.assertIn("from the Experience section", first)
        self.assertIn("Built REST APIs for mobile applications.", first)
        self.assertIn("Added unit tests for service endpoints.", first)
        self.assertNotIn("Maintained project history in GitHub.", first)
        self.assertIn("broader semantic relevance", first)
        self.assertIn(
            "Semantic relevance is stronger than explicit keyword coverage.", first
        )
        self.assertIn("52.0% final score", first)

    def test_null_evidence_and_keyword_signal_are_handled(self) -> None:
        candidate = normalize_stage2_output(current_payload())[1]
        explanation = generate_explanation(candidate)

        self.assertNotIn('Evidence for REST API: "None"', explanation)
        self.assertIn(
            "Explicit keyword coverage is stronger than overall semantic similarity.",
            explanation,
        )

    def test_empty_matches_missing_skills_and_signal_note_degrade_cleanly(self) -> None:
        candidate = normalize_stage2_output(
            [
                {
                    "candidate_id": "EMPTY",
                    "final_score": 0.25,
                    "keyword_score": 0.20,
                    "semantic_score": 0.30,
                    "matched_skills": [],
                    "missing_required_skills": [],
                    "signal_note": None,
                }
            ]
        )[0]

        explanation = generate_explanation(candidate)

        self.assertIn("No matched skills were recorded.", explanation)
        self.assertIn("No required skills were identified as missing.", explanation)
        self.assertNotIn("stronger than", explanation)


class ComparisonExtensionTests(unittest.TestCase):
    def test_comparison_adds_classified_differences_without_changing_rank_logic(self) -> None:
        candidate_a, candidate_b = normalize_stage2_output(current_payload())

        first = compare_candidates(candidate_a, candidate_b)
        second = compare_candidates(candidate_a, candidate_b)

        self.assertEqual(first, second)
        self.assertEqual(first["higher_ranked_candidate"]["candidate_id"], "C-A")
        self.assertEqual(first["rank_difference"], 1)
        self.assertEqual(first["final_score_difference"], 0.22)
        self.assertTrue(first["skill_classification_available"])
        self.assertEqual(first["candidate_a_unique_required_skills"], ["SQL"])
        self.assertEqual(first["candidate_b_unique_required_skills"], [])
        self.assertEqual(first["candidate_a_unique_preferred_skills"], ["Git"])
        self.assertEqual(first["candidate_b_unique_preferred_skills"], ["NoSQL"])
        self.assertEqual(
            first["candidate_a_unique_unclassified_skills"], ["Testing"]
        )
        self.assertIn("uniquely matched required skill SQL", generate_comparison_explanation(first))

    def test_legacy_comparison_keeps_generic_unique_skill_behavior(self) -> None:
        payload = current_payload()
        for candidate in payload["ranked_candidates"]:
            for match in candidate["matched_skills"]:
                match.pop("required", None)
        candidate_a, candidate_b = normalize_stage2_output(payload)

        comparison = compare_candidates(candidate_a, candidate_b)

        self.assertFalse(comparison["skill_classification_available"])
        self.assertEqual(
            comparison["candidate_a_unique_matched_skills"],
            ["SQL", "Git", "Testing"],
        )
        self.assertIn(
            "uniquely matched skills SQL, Git, and Testing",
            generate_comparison_explanation(comparison),
        )


if __name__ == "__main__":
    unittest.main()
