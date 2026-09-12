"""
Stage 1 — Resume Parser
Hidden-text / ATS-stuffing stripper + section splitter + skill extractor

Supports: PDF and DOCX
Output:   One resume_<id>.json per file

Usage:
  python hidden_text_strip.py <resume.pdf|docx>         # single file debug
  python hidden_text_strip.py <pdf_dir> <out_dir>       # batch mode

Requires: pip install pymupdf python-docx
"""

import fitz  # PyMuPDF
import re
import json
import os
from dataclasses import dataclass, field
from docx import Document


# ── Config ────────────────────────────────────────────────────────────────────

MIN_FONT_SIZE = 4.5
COLOR_SIMILARITY_THRESHOLD = 12
DEFAULT_BG = (255, 255, 255)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class SpanFlag:
    text: str
    reason: str
    font_size: float
    color: tuple
    bbox: tuple


@dataclass
class ExtractionResult:
    clean_text: str
    flagged_spans: list = field(default_factory=list)

    def report(self) -> str:
        if not self.flagged_spans:
            return "No hidden/stuffed text detected."
        lines = [f"Flagged {len(self.flagged_spans)} suspicious span(s):"]
        for f in self.flagged_spans:
            preview = f.text.strip()[:60].replace("\n", " ")
            lines.append(f"  - [{f.reason}] size={f.font_size:.1f}pt "
                          f"color={f.color} :: \"{preview}\"")
        return "\n".join(lines)


# ── PDF extraction ─────────────────────────────────────────────────────────────

def _int_color(color_val) -> tuple:
    if isinstance(color_val, tuple):
        return color_val
    r = (color_val >> 16) & 255
    g = (color_val >> 8) & 255
    b = color_val & 255
    return (r, g, b)


def _color_matches_bg(color: tuple, bg: tuple = DEFAULT_BG) -> bool:
    return all(abs(c - b) <= COLOR_SIMILARITY_THRESHOLD for c, b in zip(color, bg))


def extract_from_pdf(pdf_path: str) -> ExtractionResult:
    doc = fitz.open(pdf_path)
    clean_parts = []
    flagged = []

    for page in doc:
        page_rect = page.rect
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_parts = []
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue

                    size = span.get("size", 0)
                    color = _int_color(span.get("color", 0))
                    bbox = span.get("bbox", (0, 0, 0, 0))

                    reason = None
                    if size < MIN_FONT_SIZE:
                        reason = "tiny-font"
                    elif _color_matches_bg(color):
                        reason = "invisible-color"
                    elif not page_rect.intersects(fitz.Rect(bbox)):
                        reason = "off-page"

                    if reason:
                        flagged.append(SpanFlag(text, reason, size, color, bbox))
                    else:
                        line_parts.append(text)

                if line_parts:
                    clean_parts.append("".join(line_parts))

    doc.close()
    return ExtractionResult(clean_text="\n".join(clean_parts), flagged_spans=flagged)


# ── DOCX extraction ────────────────────────────────────────────────────────────

def extract_from_docx(docx_path: str) -> ExtractionResult:
    """
    DOCX hidden text: Word has a 'vanish' font property that hides text.
    We detect and strip paragraphs/runs where all runs are vanished.
    No colour check needed — DOCX hidden text uses the vanish flag, not white colour.
    """
    doc = Document(docx_path)
    clean_parts = []
    flagged = []

    for para in doc.paragraphs:
        para_text = ""
        para_flagged = False

        for run in para.runs:
            text = run.text
            if not text.strip():
                continue

            # Check vanish (hidden text) property
            vanish = False
            if run.font.hidden:
                vanish = True

            if vanish:
                flagged.append(SpanFlag(
                    text=text,
                    reason="docx-hidden",
                    font_size=run.font.size.pt if run.font.size else 0,
                    color=(0, 0, 0),
                    bbox=(0, 0, 0, 0)
                ))
                para_flagged = True
            else:
                para_text += text

        if para_text.strip():
            clean_parts.append(para_text)

    return ExtractionResult(clean_text="\n".join(clean_parts), flagged_spans=flagged)


# ── TXT extraction ─────────────────────────────────────────────────────────────

def extract_from_txt(txt_path: str) -> ExtractionResult:
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return ExtractionResult(clean_text=text, flagged_spans=[])


# ── XML extraction ─────────────────────────────────────────────────────────────

def extract_from_xml(xml_path: str) -> ExtractionResult:
    """Strip all XML tags and return inner text content only."""
    with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return ExtractionResult(clean_text=text, flagged_spans=[])


# ── Dispatcher ─────────────────────────────────────────────────────────────────

def extract_clean_text(file_path: str) -> ExtractionResult:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext == ".docx":
        return extract_from_docx(file_path)
    elif ext == ".txt":
        return extract_from_txt(file_path)
    elif ext == ".xml":
        return extract_from_xml(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ── Section splitting ──────────────────────────────────────────────────────────

SECTION_HEADERS = {
    "summary":        ["summary", "professional summary", "profile", "objective", "about me"],
    "skills":         ["skills", "technical skills", "core competencies", "technologies", "key skills"],
    "experience":     ["experience", "work experience", "professional experience",
                       "employment history", "work history", "internships", "internship"],
    "projects":       ["projects", "personal projects", "academic projects", "technical projects",
                       "key projects"],
    "education":      ["education", "academic background", "qualifications", "academic qualifications"],
    "certifications": ["certifications", "certificates", "courses", "certifications & courses"],
    "achievements":   ["achievements", "awards", "achievements & awards", "honours", "honors",
                       "extracurricular activities", "extracurricular", "activities"],
}

_HEADER_LOOKUP = {}
for canonical, variants in SECTION_HEADERS.items():
    for v in variants:
        _HEADER_LOOKUP[v] = canonical


def _looks_like_header(line: str) -> str | None:
    normalized = line.strip().lower().strip(":").strip()
    if not normalized or len(normalized) > 50:
        return None
    return _HEADER_LOOKUP.get(normalized)


def split_into_sections(clean_text: str) -> dict:
    sections = {name: [] for name in SECTION_HEADERS}
    current = None

    for line in clean_text.split("\n"):
        header = _looks_like_header(line)
        if header:
            current = header
            continue
        if current:
            sections[current].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


# ── Skill extraction ───────────────────────────────────────────────────────────

# Extend this list once you have the actual JD
# Skills drawn from the actual JD (TechNova — Junior Full Stack Developer Intern)
# MUST-HAVE from JD
JD_REQUIRED = [
    "javascript", "react", "node.js", "express", "rest apis", "json",
    "mysql", "postgresql", "mongodb", "git", "github",
]

# GOOD-TO-HAVE from JD
JD_NICE_TO_HAVE = [
    "typescript", "aws", "gcp", "azure", "docker", "jest", "mocha", "agile", "scrum",
]

SKILL_VOCAB = [
    # === JD MUST-HAVE (match these first — highest signal) ===
    "javascript", "react", "node.js", "express", "rest apis", "json",
    "mysql", "postgresql", "mongodb", "git", "github",
    # === JD GOOD-TO-HAVE ===
    "typescript", "aws", "gcp", "azure", "docker", "jest", "mocha", "agile", "scrum",
    # === General full-stack / CS skills ===
    "python", "java", "c++", "sql", "go", "ruby", "php", "swift",
    "dart", "kotlin", "bash", "powershell",
    "vue", "angular", "html", "css", "next.js", "tailwind", "react native",
    "flutter", "android", "ios", "firebase",
    "django", "flask", "fastapi", "spring boot",
    "redis", "sqlite", "firestore",
    "kubernetes", "linux", "ci/cd", "terraform", "gitlab", "jenkins",
    "graphql", "websockets",
    # === Cyber (present in some resumes) ===
    "burp suite", "owasp", "penetration testing", "nmap", "wireshark", "metasploit",
    "sqlmap", "splunk", "kali linux", "vulnerability assessment", "vapt",
    # === Data / ML ===
    "pandas", "numpy", "tensorflow", "pytorch", "machine learning", "scikit-learn",
    "scapy", "opencv",
    # === Tools ===
    "postman", "figma", "jira", "virtualbox",
]


def extract_skills(text: str, vocab: list = SKILL_VOCAB) -> list:
    normalized = re.sub(r"[^\w\s+.#/-]", " ", text.lower())
    found = []
    for skill in vocab:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized):
            found.append(skill)
    return found


# ── Full pipeline ──────────────────────────────────────────────────────────────

def parse_education(raw_text: str) -> dict:
    """Extract degree, institution, year range, and CGPA/GPA from education raw text."""
    result = {
        "degree": "",
        "institution": "",
        "year": "",
        "cgpa": "",
        "raw_text": raw_text,
    }
    if not raw_text:
        return result

    # CGPA / GPA
    cgpa_match = re.search(r"(?:cgpa|gpa)[:\s]*([0-9]+\.[0-9]+)\s*(?:/\s*[0-9]+)?", raw_text, re.IGNORECASE)
    if cgpa_match:
        result["cgpa"] = cgpa_match.group(1)

    # Year range e.g. 2022-2026 or 2022 – 2026
    year_match = re.search(r"(20\d{2})\s*[-–]\s*(20\d{2}|present|expected)", raw_text, re.IGNORECASE)
    if year_match:
        result["year"] = f"{year_match.group(1)}-{year_match.group(2)}"

    # Degree — look for common degree prefixes
    degree_match = re.search(
        r"(b\.?tech|b\.?e\.?|b\.?sc\.?|m\.?tech|m\.?sc\.?|bca|mca|b\.?com)[^,\n]*",
        raw_text, re.IGNORECASE
    )
    if degree_match:
        result["degree"] = degree_match.group(0).strip()

    # Institution — line or segment after the degree or on its own line
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    for line in lines:
        # institution lines usually contain "Institute", "College", "University", "School", "NIT", "IIT"
        if re.search(r"(institute|college|university|school|nit|iit|manipal|symbiosis|rv |vit )", line, re.IGNORECASE):
            inst = re.sub(r"^(b\.?tech|b\.?e\.?|b\.?sc\.?|m\.?tech|bca|mca)[^,]*,\s*", "", line, flags=re.IGNORECASE)
            inst = re.sub(r"\s*[\(\[]?20\d{2}.*$", "", inst).strip().rstrip(",")
            result["institution"] = inst
            break

    return result


def build_resume_json(file_path: str, resume_id: str) -> dict:
    result = extract_clean_text(file_path)
    sections_raw = split_into_sections(result.clean_text)

    sections = {}
    for name, raw_text in sections_raw.items():
        if name == "education":
            sections[name] = parse_education(raw_text)
        else:
            sections[name] = {
                "raw_text": raw_text,
                "extracted_skills": extract_skills(raw_text) if name in ("skills", "experience", "projects") else [],
            }

    # Extract candidate name from first non-empty line
    candidate_name = ""
    for line in result.clean_text.split("\n"):
        line = line.strip()
        if line and len(line) < 60:
            candidate_name = line
            break

    return {
        "resume_id": resume_id,
        "candidate_name": candidate_name,
        "source_filename": os.path.basename(file_path),
        "sections": sections,
        "full_text_clean": result.clean_text,
        "integrity": {
            "hidden_spans_stripped": len(result.flagged_spans),
            "reasons": sorted(set(f.reason for f in result.flagged_spans)),
        },
    }


def process_batch(input_dir: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    supported = (".pdf", ".docx", ".txt", ".xml")
    files = [f for f in sorted(os.listdir(input_dir)) if f.lower().endswith(supported)]

    if not files:
        print(f"No PDF or DOCX files found in {input_dir}")
        return

    for fname in files:
        resume_id = os.path.splitext(fname)[0]
        file_path = os.path.join(input_dir, fname)
        try:
            data = build_resume_json(file_path, resume_id)
            out_path = os.path.join(out_dir, f"{resume_id}.json")
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2)
            stripped = data["integrity"]["hidden_spans_stripped"]
            print(f"[OK] {fname}  →  {resume_id}.json  (stripped {stripped} hidden span(s))")
        except Exception as e:
            print(f"[ERR] {fname}: {e}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1].lower().endswith((".pdf", ".docx", ".txt", ".xml")):
        path = sys.argv[1]
        result = extract_clean_text(path)
        print(result.report())
        data = build_resume_json(path, os.path.splitext(os.path.basename(path))[0])
        print(json.dumps(data, indent=2))

    elif len(sys.argv) == 3:
        process_batch(sys.argv[1], sys.argv[2])

    else:
        print("Usage:")
        print("  python hidden_text_strip.py <resume.pdf|docx>      # single file, debug")
        print("  python hidden_text_strip.py <input_dir> <out_dir>  # batch mode")
        sys.exit(1)