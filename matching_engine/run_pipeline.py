"""run_pipeline.py — rank resumes against ANY job description."""

import json
import re
import sys

from adapter import load_resumes, extract_skills_from_text
from matching import rank_candidates, SYNONYM_MAP

PARSED_DIR = r"D:\DEV\Apex\data\parsed"
OUTPUT_FILE = "ranked_output.json"

REQUIRED_HEADINGS = ["must-have", "must have", "required skills", "requirements",
                     "minimum qualifications", "essential skills", "key skills"]
OPTIONAL_HEADINGS = ["good-to-have", "good to have", "nice-to-have", "nice to have",
                     "preferred", "bonus", "desirable", "plus", "optional"]
CONTEXT_HEADINGS = ["responsibilities", "key responsibilities", "what you'll do",
                    "about the role", "role overview"]
IGNORE_HEADINGS = ["soft skills", "benefits", "perks", "about us", "how to apply"]

CATEGORY_MEMBERS = {
    "Frontend": {"react", "react.js", "reactjs", "vue", "vue.js", "angular",
                 "svelte", "next.js", "jquery"},
    "Database": {"sql", "nosql", "mysql", "postgresql", "postgres", "mongodb",
                 "sqlite", "mariadb", "dynamodb", "firebase", "oracle"},
    "Cloud": {"aws", "azure", "gcp", "google cloud", "amazon web services"},
    "Testing": {"jest", "mocha", "pytest", "junit", "selenium", "chai"},
}
CHOICE_CUES = ["or similar", "at least one", "one of", "such as", "e.g.",
               "preferred", "any of", "or equivalent", " or "]


def _classify(line):
    t = line.strip().lower().rstrip(":")
    if len(t) > 60:
        return None
    for g, names in (("required", REQUIRED_HEADINGS), ("optional", OPTIONAL_HEADINGS),
                     ("ignore", IGNORE_HEADINGS), ("context", CONTEXT_HEADINGS)):
        for n in names:
            if n in t:
                return g
    return None


def _split(txt):
    b = {"required": [], "optional": [], "context": [], "ignore": []}
    cur = None
    for line in txt.splitlines():
        h = _classify(line)
        if h:
            cur = h
            continue
        if cur:
            b[cur].append(line)
    if not any(b[k] for k in ("required", "optional")):
        b["context"] = txt.splitlines()
    return {k: "\n".join(v) for k, v in b.items()}


ALIAS_INDEX = {}
for _c, _al in SYNONYM_MAP.items():
    for _a in _al:
        if _a not in SYNONYM_MAP:
            ALIAS_INDEX.setdefault(_a.lower(), _c)


def _canon(skills):
    seen, out = set(), []
    for s in skills:
        c = ALIAS_INDEX.get(s.lower(), s)
        if c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def _rollup(skills, text):
    low = {s.lower() for s in skills}
    res, demoted, used = [], [], set()
    cue = any(c in text.lower() for c in CHOICE_CUES)
    for cat, members in CATEGORY_MEMBERS.items():
        present = low & members
        if present and (len(present) > 1 or cue):
            res.append(cat)
            used |= present
            demoted.extend(s for s in skills if s.lower() in present)
    for s in skills:
        if s.lower() not in used:
            res.append(s)
    seen, out = set(), []
    for s in res:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out, demoted


def parse_jd(text):
    sec = _split(text)
    req = extract_skills_from_text(sec["required"])
    opt = extract_skills_from_text(sec["optional"])
    ctx = extract_skills_from_text(sec["context"])
    known = {s.lower() for s in req + opt}
    req = req + [s for s in ctx if s.lower() not in known]

    required, demoted = _rollup(req, sec["required"] + "\n" + sec["context"])
    optional = list(opt)
    for s in demoted:
        if s.lower() not in {o.lower() for o in optional}:
            optional.append(s)

    required = _canon(required)
    optional = _canon(optional)
    rl = {s.lower() for s in required}
    optional = [s for s in optional if s.lower() not in rl]

    print("\n--- JD PARSED AUTOMATICALLY ---")
    print(f"  required : {', '.join(required) or '(none)'}")
    print(f"  optional : {', '.join(optional) or '(none)'}")
    if demoted:
        print(f"  rolled up: {', '.join(demoted)} -> category (JD offers a choice)")

    return {"full_text": " ".join(text.split()),
            "required_skills": required,
            "nice_to_have_skills": optional}


def load_jd(path):
    if path.lower().endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    else:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    return parse_jd(text)


def main():
    if "--jd" not in sys.argv:
        print("Usage: python run_pipeline.py --jd <path to JD .pdf or .txt> [--save]")
        raise SystemExit(1)

    jd_path = sys.argv[sys.argv.index("--jd") + 1]
    print(f"Reading JD: {jd_path}")
    jd = load_jd(jd_path)

    print("\nLoading parsed resumes...")
    resumes = load_resumes(PARSED_DIR)
    if not resumes:
        print(f"No resumes found in {PARSED_DIR}")
        return
    print(f"Loaded {len(resumes)} resumes.")

    fb = [r for r in resumes if r.get("_parse_quality") == "fulltext_fallback"]
    if fb:
        print(f"  note: {len(fb)}/{len(resumes)} fell back to full-text matching.")

    print("\nScoring...\n")
    ranked = rank_candidates(jd, resumes)
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
            print(f"        missing: {', '.join(m['skill'] for m in r['missing_required_skills'])}")

    s = [r["final_score"] for r in ranked]
    print("\n" + "-" * 72)
    print(f"spread: {min(s):.4f} to {max(s):.4f}  (range {max(s) - min(s):.4f})")
    print("-" * 72)

    if "--save" in sys.argv:
        clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in ranked]
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2)
        print(f"\nWrote {OUTPUT_FILE}\n")


if __name__ == "__main__":
    main()