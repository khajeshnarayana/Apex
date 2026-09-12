"""
tune_weights.py — compare fusion options against the real dataset resumes.

The problem we're solving:
    Sahil (Sales) scored semantic 0.4229 — HIGHER than Siddharth (App Dev, 0.3427).
    Cause: every resume in this dataset shares heavy boilerplate (same company,
    same "improved X by Y%" bullet style, same certifications), so the embedding
    model reads them all as "student intern resume" regardless of domain.

    His keyword score of 0.0 saves him, but only by a thin margin.

Options tested:
    A) Shift fusion weights toward keyword (the more discriminating signal here)
    B) Apply a floor rule: zero required-skill matches caps the final score
    C) Both together

Run:  python tune_weights.py
"""

import matching
from test_real_resumes import PLACEHOLDER_JD, REAL_RESUMES


# ---------------------------------------------------------------------------
# Option B: floor rule
# ---------------------------------------------------------------------------

def apply_floor(results, cap=0.15):
    """
    A candidate matching ZERO required skills cannot rank as a partial match.
    Their score gets capped, so they cannot drift up on semantic similarity alone.

    Rationale for judges: semantic similarity tells you a resume *reads* related.
    It does not tell you the candidate can do the job. If none of the required
    skills are present in any form — not even via synonym — that is a hard signal
    no amount of stylistic similarity should override.
    """
    for r in results:
        if not r["matched_skills"]:
            r["final_score"] = min(r["final_score"], cap)
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

def run(kw_weight, sem_weight, floor=False, label=""):
    matching.KEYWORD_WEIGHT = kw_weight
    matching.SEMANTIC_WEIGHT = sem_weight

    results = matching.rank_candidates(PLACEHOLDER_JD, REAL_RESUMES)
    if floor:
        results = apply_floor(results)

    print(f"\n{'=' * 72}")
    print(f"{label}   (keyword={kw_weight}, semantic={sem_weight}"
          f"{', floor rule ON' if floor else ''})")
    print("=" * 72)

    for i, r in enumerate(results, 1):
        n_matched = len(r["matched_skills"])
        print(f"  #{i}  {r['name']:<18} {r['final_score']:.4f}   "
              f"(kw {r['keyword_score']:.3f} / sem {r['semantic_score']:.3f})   "
              f"{n_matched} skills matched")

    scores = [r["final_score"] for r in results]
    spread = round(max(scores) - min(scores), 4)

    # The key diagnostic: how far is the best non-technical candidate
    # from the worst actual developer?
    dev_names = {"Aditya Joshi", "Karan Malhotra", "Siddharth Rao"}
    dev_scores = [r["final_score"] for r in results if r["name"] in dev_names]
    nondev_scores = [r["final_score"] for r in results if r["name"] not in dev_names]

    worst_dev = min(dev_scores)
    best_nondev = max(nondev_scores)
    gap = round(worst_dev - best_nondev, 4)

    print(f"\n  spread (top to bottom):        {spread}")
    print(f"  worst developer:               {worst_dev:.4f}")
    print(f"  best non-developer:            {best_nondev:.4f}")
    print(f"  >> SEPARATION GAP:             {gap:.4f}   "
          f"{'<-- GOOD' if gap > 0.15 else '<-- too close for comfort'}")

    return gap


if __name__ == "__main__":
    print("\nGoal: widen the gap between real developers and domain-mismatched")
    print("candidates, without breaking the ordering among the developers.\n")

    results = {}

    results["current"] = run(0.4, 0.6, False, "CURRENT (baseline)")
    results["balanced"] = run(0.5, 0.5, False, "OPTION A1 — balanced")
    results["kw_heavy"] = run(0.6, 0.4, False, "OPTION A2 — keyword-leaning")
    results["floor_only"] = run(0.4, 0.6, True, "OPTION B — floor rule only")
    results["both"] = run(0.6, 0.4, True, "OPTION C — keyword-leaning + floor")

    print("\n" + "=" * 72)
    print("SUMMARY — separation gap by option (higher is better)")
    print("=" * 72)
    for name, gap in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {name:<14} {gap:.4f}")
    print()
    print("Pick based on the gap, but sanity-check that developer ORDERING")
    print("stayed sensible in the detail above — a big gap is worthless if it")
    print("scrambled the ranking among the candidates who actually qualify.")
    print()