"""
parse_resumes.py — FALLBACK resume parser.

Person 1 owns parsing. This exists only so the matching side is never
blocked waiting for it: point it at a folder of resume PDFs and it writes
JSON in the same shape Person 1's parser produces, which the adapter
already understands.

If Person 1's output is available, use theirs — it is better tested.

Usage:
    pip install pdfplumber
    python parse_resumes.py "D:\\DEV\\Apex\\data\\Testing Dataset" "D:\\DEV\\Apex\\data\\parsed"
"""

import json
import os
import re
import sys


# Headings resumes actually use, mapped to the section names the adapter wants.
SECTION_ALIASES = {
    "summary": [
        "summary", "professional summary", "profile", "objective",
        "career objective", "about me",
    ],
    "skills": [
        "skills", "technical skills", "core skills", "tech stack",
        "technologies", "skills & tools", "technical proficiencies",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment", "internships", "internship experience", "work history",
    ],
    "projects": [
        "projects", "personal projects", "academic projects",
        "key projects", "selected projects",
    ],
    "education": [
        "education", "academic background", "qualifications",
        "academic qualifications",
    ],
    "certifications": [
        "certifications", "certificates", "courses", "licenses",
    ],
    "achievements": [
        "achievements", "awards", "achievements & awards", "honors",
        "extracurricular activities", "extracurricular", "activities",
        "accomplishments",
    ],
}


def clean_text(text):
    """Strip PDF extraction artefacts."""
    # pdfplumber renders bullets as (cid:NNN)
    text = re.sub(r"\(cid:\d+\)", "", text)
    # Collapse runs of spaces but keep line structure
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf(path):
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return clean_text("\n".join(pages))


def _match_heading(line):
    """Return the canonical section name if this line is a heading."""
    text = line.strip().rstrip(":").lower()
    if not text or len(text) > 45:
        return None
    # Headings are short standalone lines, usually caps or title case
    if len(text.split()) > 5:
        return None
    for canonical, aliases in SECTION_ALIASES.items():
        if text in aliases:
            return canonical
    return None


def split_sections(text):
    """Split resume text into named sections."""
    sections = {name: [] for name in SECTION_ALIASES}
    current = None

    for line in text.splitlines():
        heading = _match_heading(line)
        if heading:
            current = heading
            continue
        if current:
            sections[current].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def guess_name(text):
    """The first non-empty line of a resume is almost always the name."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.search(r"[@|]|\d{4}|http", line):
            continue
        if 2 <= len(line.split()) <= 5 and len(line) < 50:
            return line.title() if line.isupper() else line
        break
    return ""


def parse_resume(path):
    """Parse one resume PDF into Person 1's JSON shape."""
    text = read_pdf(path)
    sections = split_sections(text)
    resume_id = os.path.splitext(os.path.basename(path))[0]

    return {
        "resume_id": resume_id,
        "candidate_name": guess_name(text),
        "source_filename": os.path.basename(path),
        "sections": {
            name: {"raw_text": content, "extracted_skills": []}
            for name, content in sections.items()
        },
        "full_text_clean": text,
        "integrity": {"hidden_spans_stripped": 0, "reasons": []},
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)

    in_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    pdfs = [f for f in sorted(os.listdir(in_dir)) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"No PDFs found in {in_dir}")
        return

    print(f"Parsing {len(pdfs)} resumes...\n")
    ok = 0

    for filename in pdfs:
        try:
            data = parse_resume(os.path.join(in_dir, filename))
            out_path = os.path.join(out_dir, os.path.splitext(filename)[0] + ".json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            filled = [
                n for n, s in data["sections"].items()
                if s["raw_text"] and n in ("skills", "experience", "projects")
            ]
            status = ", ".join(filled) if filled else "NO SECTIONS (will use full text)"
            print(f"  {data['candidate_name'] or filename:28} -> {status}")
            ok += 1
        except Exception as e:
            print(f"  !! {filename}: {e}")

    print(f"\nWrote {ok} JSON files to {out_dir}")


if __name__ == "__main__":
    main()