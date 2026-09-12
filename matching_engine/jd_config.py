"""jd_parser.py — turn ANY job description into skill lists automatically."""

import re
import sys
try:
    from .adapter import extract_skills_from_text
    from .matching import SYNONYM_MAP
except ImportError:  # Preserve standalone execution from matching_engine/.
    from adapter import extract_skills_from_text
    from matching import SYNONYM_MAP

REQUIRED_HEADINGS = ["must-have", "must have", "required skills", "requirements",
                     "minimum qualifications", "essential skills", "key skills",
                     "what you need", "you should have"]
OPTIONAL_HEADINGS = ["good-to-have", "good to have", "nice-to-have", "nice to have",
                     "preferred", "bonus", "desirable", "plus", "optional"]
CONTEXT_HEADINGS = ["responsibilities", "key responsibilities", "what you'll do",
                    "about the role", "role overview"]
IGNORE_HEADINGS = ["soft skills", "benefits", "perks", "about us", "how to apply",
                   "compensation", "salary"]

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


def _normalize_heading(line):
    """Canonicalize heading separators without changing JD body content."""
    normalized = re.sub(r"[-_–—]+", " ", line.casefold())
    return re.sub(r"\s+", " ", normalized).strip().rstrip(":").strip()


def _classify_heading(line):
    t = _normalize_heading(line)
    if len(t) > 60:
        return None
    for group, names in (("required", REQUIRED_HEADINGS),
                         ("optional", OPTIONAL_HEADINGS),
                         ("ignore", IGNORE_HEADINGS),
                         ("context", CONTEXT_HEADINGS)):
        for n in names:
            if _normalize_heading(n) in t:
                return group
    return None


def split_jd_sections(jd_text):
    buckets = {"required": [], "optional": [], "context": [], "ignore": []}
    current = None
    for line in jd_text.splitlines():
        h = _classify_heading(line)
        if h:
            current = h
            continue
        if current:
            buckets[current].append(line)
    if not any(buckets[k] for k in ("required", "optional")):
        buckets["context"] = jd_text.splitlines()
    return {k: "\n".join(v) for k, v in buckets.items()}


def _build_alias_index():
    idx = {}
    for canonical, aliases in SYNONYM_MAP.items():
        for a in aliases:
            if a not in SYNONYM_MAP:
                idx.setdefault(a.lower(), canonical)
    return idx


ALIAS_INDEX = _build_alias_index()


def _canonicalize(skills):
    seen, out = set(), []
    for s in skills:
        c = ALIAS_INDEX.get(s.lower(), s)
        if c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def _rollup(skills, section_text):
    lowered = {s.lower() for s in skills}
    result, demoted, consumed = [], [], set()
    has_cue = any(c in section_text.lower() for c in CHOICE_CUES)
    for category, members in CATEGORY_MEMBERS.items():
        present = lowered & members
        if not present:
            continue
        if len(present) > 1 or has_cue:
            result.append(category)
            consumed |= present
            demoted.extend(s for s in skills if s.lower() in present)
    for s in skills:
        if s.lower() not in consumed:
            result.append(s)
    seen, ordered = set(), []
    for s in result:
        if s.lower() not in seen:
            seen.add(s.lower())
            ordered.append(s)
    return ordered, demoted


def parse_jd(jd_text, verbose=False):
    sec = split_jd_sections(jd_text)
    req_raw = extract_skills_from_text(sec["required"])
    opt_raw = extract_skills_from_text(sec["optional"])
    ctx_raw = extract_skills_from_text(sec["context"])

    known = {s.lower() for s in req_raw + opt_raw}
    req_raw = req_raw + [s for s in ctx_raw if s.lower() not in known]

    required, demoted = _rollup(req_raw, sec["required"] + "\n" + sec["context"])
    optional = list(opt_raw)
    for s in demoted:
        if s.lower() not in {o.lower() for o in optional}:
            optional.append(s)

    required = _canonicalize(required)
    optional = _canonicalize(optional)
    req_lower = {s.lower() for s in required}
    optional = [s for s in optional if s.lower() not in req_lower]

    if verbose:
        print("\n--- JD PARSE ---")
        print(f"  required : {', '.join(required) or '(none)'}")
        print(f"  optional : {', '.join(optional) or '(none)'}")
        if demoted:
            print(f"  rolled up: {', '.join(demoted)} -> category requirement")
        print()

    return {"full_text": " ".join(jd_text.split()),
            "required_skills": required,
            "nice_to_have_skills": optional}


def parse_jd_from_pdf(path, verbose=False):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    return parse_jd(text, verbose=verbose)


def parse_jd_from_file(path, verbose=False):
    if path.lower().endswith(".pdf"):
        return parse_jd_from_pdf(path, verbose=verbose)
    with open(path, "r", encoding="utf-8") as f:
        return parse_jd(f.read(), verbose=verbose)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python jd_parser.py <jd file>")
        raise SystemExit(1)
    parse_jd_from_file(sys.argv[1], verbose=True)
