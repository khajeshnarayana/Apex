"""
run_pipeline.py — the real end-to-end run.

    Person 1's parsed JSON  ->  adapter  ->  matching engine  ->  ranked output

This is what Person 3's UI will eventually call. Running it now proves the
whole chain works on real data before the actual JD arrives.

Usage:
    python run_pipeline.py                 # ranks and prints
    python run_pipeline.py --save          # also writes ranked_output.json
"""

import json
import sys

from adapter import load_resumes
from matching import rank_candidates

PARSED_DIR = r"D:\DEV\Apex\data\parsed"
OUTPUT_FILE = "ranked_output.json"


# ---------------------------------------------------------------------------
# Placeholder JD — REPLACE THIS when the real Sample_JD drops.
# Only two things need changing: full_text, and the two skill lists.
# ---------------------------------------------------------------------------

JD = {
    "full_text": (
        "Junior Full Stack Developer Intern at TechNova Solutions. "
        "We are looking for a student or recent graduate to help build and "
        "maintain web applications end to end. You will work on backend APIs, "
        "connect them to databases, and contribute to frontend interfaces. "
        "Required: strong programming fundamentals, experience building REST APIs, "
        "working with relational or NoSQL databases, and version control with Git. "
        "Familiarity with containerisation and cloud deployment is a plus. "
        "You should be comfortable writing tests and working in an Agile team."
    ),
    "required_skills": [
        "REST API",
        "SQL",
        "Git",
        "Docker",
        "JavaScript",
    ],
    "nice_to_have_skills": [
        "AWS",
        "Testing",
        "Agile",
        "NoSQL",
    ],
}


def main():
    print("\nLoading parsed resumes...")
    resumes = load_resumes(PARSED_DIR)

    if not resumes:
        print(f"No resumes found in {PARSED_DIR}")
        print("Check the path, or wait for Person 1's output.")
        return

    print(f"Loaded {len(resumes)} resumes.")

    # Parse-quality report — worth knowing how much of the batch
    # fell back to whole-document matching.
    fallback = [r for r in resumes if r.get("_parse_quality") == "fulltext_fallback"]
    if fallback:
        pct = round(100 * len(fallback) / len(resumes))
        print(f"  note: {len(fallback)}/{len(resumes)} ({pct}%) had no usable sections "
              f"and fell back to full-text matching.")

    print("\nScoring against JD...\n")
    ranked = rank_candidates(JD, resumes)

    # Add the rank field Person 3 asked about.
    for i, r in enumerate(ranked, 1):
        r["rank"] = i

    print("=" * 72)
    print("RANKED SHORTLIST")
    print("=" * 72)

    for r in ranked:
        print(f"\n#{r['rank']}  {r['name']}")
        print(f"     FINAL {r['final_score']:.4f}   "
              f"(keyword {r['keyword_score']:.3f} / semantic {r['semantic_score']:.3f})")

        if r["matched_skills"]:
            for m in r["matched_skills"]:
                extra = f"  <- '{m['found_as']}'" if m["match_type"] == "synonym" else ""
                print(f"        + {m['skill']} [{m['match_type']}]{extra}")
        else:
            print("        (no required skills matched)")

        if r["missing_required_skills"]:
            missing_names = [m["skill"] for m in r["missing_required_skills"]]
            print(f"        missing: {', '.join(missing_names)}")

    scores = [r["final_score"] for r in ranked]
    print("\n" + "-" * 72)
    print(f"spread: {min(scores):.4f} to {max(scores):.4f}  "
          f"(range {max(scores) - min(scores):.4f})")
    print("-" * 72)

    if "--save" in sys.argv:
        # Strip internal fields before handing to Person 3.
        clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in ranked]
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2)
        print(f"\nWrote {OUTPUT_FILE} — this is what Person 3's UI consumes.\n")


if __name__ == "__main__":
    main()