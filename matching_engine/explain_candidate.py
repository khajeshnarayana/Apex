"""
explain_candidate.py — full scoring trace for a single candidate.

Built for the judging walkthrough. The problem statement says judges will
ask each team to explain how their matching actually works, so rather than
describing it from memory, this prints the complete arithmetic: every
required skill, whether it matched, how it matched, which section it came
from, the sentence proving it, and how the numbers combine into the final
score.

Usage:
    python explain_candidate.py                 # walks through the #1 candidate
    python explain_candidate.py 3               # walks through the #3 candidate
    python explain_candidate.py Aditya          # walks through by name (partial ok)
    python explain_candidate.py --compare 1 2   # why is #1 above #2?
"""

import sys

from adapter import load_resumes
from jd_config import JD
from matching import (
    KEYWORD_WEIGHT,
    SECTION_WEIGHTS,
    SEMANTIC_WEIGHT,
    SYNONYM_MAP,
    rank_candidates,
)
from run_pipeline import PARSED_DIR


LINE = "=" * 74
THIN = "-" * 74


def _fmt_section(name):
    """Human-readable section label plus the weight it carries."""
    labels = {
        "projects": "Projects",
        "experience": "Experience",
        "skills_section": "Skills list",
        "certifications": "Certifications",
        "achievements": "Achievements",
        "full_text": "Whole document (sections unavailable)",
    }
    weight = SECTION_WEIGHTS.get(name, 0)
    return f"{labels.get(name, name)} (weight {weight})"


def walkthrough(candidate, rank):
    """Print the full scoring story for one candidate."""
    required = JD.get("required_skills", [])
    nice = JD.get("nice_to_have_skills", [])

    matched = candidate["matched_skills"]
    matched_required = [m for m in matched if m.get("required")]
    matched_nice = [m for m in matched if not m.get("required")]
    missing = candidate["missing_required_skills"]

    print(f"\n{LINE}")
    print(f"  #{rank}  {candidate['name']}")
    print(f"  final score {candidate['final_score']}")
    print(LINE)

    # ---- Step 1: keyword side -------------------------------------------
    print("\nSTEP 1 — KEYWORD MATCHING")
    print("We check every skill the JD asks for against this resume, allowing")
    print("known equivalents. Where a skill was found matters: a skill shown")
    print("in a project counts more than one merely listed.\n")

    print(f"  Required skills in this JD ({len(required)}): {', '.join(required)}\n")

    for m in matched_required:
        print(f"  [FOUND]   {m['skill']}")
        if m["match_type"] == "synonym":
            print(f"            matched via '{m['found_as']}' — a known equivalent")
        else:
            print(f"            stated directly as '{m['found_as']}'")
        print(f"            source: {_fmt_section(m.get('found_in'))}")
        if m.get("evidence"):
            print(f"            evidence: \"{m['evidence']}\"")
        print()

    for m in missing:
        note = ""
        if m.get("semantic_hint"):
            note = "  (resume reads as related overall, so may be phrased differently)"
        print(f"  [MISSING] {m['skill']}{note}")

    if matched_nice:
        print(f"\n  Nice-to-have skills also found: "
              f"{', '.join(m['skill'] for m in matched_nice)}")

    n_req_found = len(matched_required)
    print(f"\n  -> matched {n_req_found} of {len(required)} required skills")
    print(f"  -> KEYWORD SCORE: {candidate['keyword_score']}")
    print("     (required skills carry 85% of this, nice-to-haves 15%)")

    # ---- Step 2: semantic side ------------------------------------------
    print(f"\n{THIN}")
    print("\nSTEP 2 — SEMANTIC MATCHING")
    print("Separately, we convert the JD and the resume into numerical vectors")
    print("using a sentence-embedding model, then measure how close they are.")
    print("This catches relevant experience described in words the JD never uses.\n")
    print(f"  -> SEMANTIC SCORE: {candidate['semantic_score']}")

    if candidate.get("signal_note") == "semantic_above_keyword":
        print("\n  NOTE: semantic scores much higher than keyword here. The resume")
        print("  reads as relevant but doesn't use this JD's specific vocabulary —")
        print("  worth a human second look.")
    elif candidate.get("signal_note") == "keyword_above_semantic":
        print("\n  NOTE: keyword scores much higher than semantic here. The right")
        print("  terms appear, but the surrounding work description is less")
        print("  aligned — worth checking the skills are genuinely demonstrated.")

    # ---- Step 3: fusion --------------------------------------------------
    kw = candidate["keyword_score"]
    sem = candidate["semantic_score"]
    print(f"\n{THIN}")
    print("\nSTEP 3 — COMBINING THE TWO")
    print("Neither signal alone is enough. Keyword matching alone misses people")
    print("who phrase things differently; semantic matching alone can't tell a")
    print("genuinely qualified candidate from one who merely writes a similar")
    print("sort of resume. So we weight them and add.\n")
    print(f"  final = {KEYWORD_WEIGHT} x keyword  +  {SEMANTIC_WEIGHT} x semantic")
    print(f"        = {KEYWORD_WEIGHT} x {kw}  +  {SEMANTIC_WEIGHT} x {sem}")
    print(f"        = {round(KEYWORD_WEIGHT * kw, 4)}  +  {round(SEMANTIC_WEIGHT * sem, 4)}")
    print(f"        = {candidate['final_score']}")
    print("\n  The 60/40 split wasn't guessed — we tested five weightings against")
    print("  resumes from unrelated fields and picked the one that separated")
    print("  qualified candidates most cleanly.")
    print(f"\n{LINE}\n")


def compare(a, b, rank_a, rank_b):
    """Explain why one candidate outranks another."""
    print(f"\n{LINE}")
    print(f"  WHY IS #{rank_a} {a['name'].upper()} RANKED ABOVE "
          f"#{rank_b} {b['name'].upper()}?")
    print(LINE)

    diff = round(a["final_score"] - b["final_score"], 4)
    print(f"\n  {a['name']}: {a['final_score']}   vs   "
          f"{b['name']}: {b['final_score']}   (gap {diff})\n")

    kw_diff = round(a["keyword_score"] - b["keyword_score"], 4)
    sem_diff = round(a["semantic_score"] - b["semantic_score"], 4)

    print(f"  keyword:   {a['keyword_score']} vs {b['keyword_score']}   "
          f"(difference {kw_diff:+})")
    print(f"  semantic:  {a['semantic_score']} vs {b['semantic_score']}   "
          f"(difference {sem_diff:+})")

    kw_contrib = abs(KEYWORD_WEIGHT * kw_diff)
    sem_contrib = abs(SEMANTIC_WEIGHT * sem_diff)
    if kw_contrib > sem_contrib:
        print("\n  -> The gap is driven mainly by SKILL COVERAGE.")
    elif sem_contrib > kw_contrib:
        print("\n  -> The gap is driven mainly by OVERALL RELEVANCE of the")
        print("     experience described, rather than specific skill terms.")
    else:
        print("\n  -> Both signals contribute about equally to the gap.")

    a_skills = {m["skill"] for m in a["matched_skills"] if m.get("required")}
    b_skills = {m["skill"] for m in b["matched_skills"] if m.get("required")}

    only_a = a_skills - b_skills
    only_b = b_skills - a_skills
    both = a_skills & b_skills

    if both:
        print(f"\n  Both have: {', '.join(sorted(both))}")
    if only_a:
        print(f"  Only {a['name']} has: {', '.join(sorted(only_a))}")
    if only_b:
        print(f"  Only {b['name']} has: {', '.join(sorted(only_b))}")

    if diff < 0.02:
        print("\n  NOTE: these two are very close. Treat them as effectively tied")
        print("  rather than genuinely ranked one above the other.")

    print(f"\n{LINE}\n")


def main():
    resumes = load_resumes(PARSED_DIR)
    if not resumes:
        print(f"No resumes found in {PARSED_DIR}")
        return

    ranked = rank_candidates(JD, resumes)

    args = [a for a in sys.argv[1:]]

    if "--compare" in args:
        rest = [a for a in args if a != "--compare"]
        if len(rest) < 2:
            print("Usage: python explain_candidate.py --compare 1 2")
            return
        i, j = int(rest[0]) - 1, int(rest[1]) - 1
        if not (0 <= i < len(ranked) and 0 <= j < len(ranked)):
            print(f"Ranks must be between 1 and {len(ranked)}.")
            return
        compare(ranked[i], ranked[j], i + 1, j + 1)
        return

    if not args:
        walkthrough(ranked[0], 1)
        return

    target = args[0]

    if target.isdigit():
        idx = int(target) - 1
        if not 0 <= idx < len(ranked):
            print(f"Rank must be between 1 and {len(ranked)}.")
            return
        walkthrough(ranked[idx], idx + 1)
        return

    # Match by name fragment
    for i, r in enumerate(ranked):
        if target.lower() in (r["name"] or "").lower():
            walkthrough(r, i + 1)
            return

    print(f"No candidate matching '{target}'. Available:")
    for i, r in enumerate(ranked, 1):
        print(f"  {i}. {r['name']}")


if __name__ == "__main__":
    main()