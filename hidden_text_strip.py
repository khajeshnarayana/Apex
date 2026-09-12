"""
Hidden-text / ATS-stuffing stripper for resume PDFs.

Detects and removes text spans that are:
  - Below a minimum visible font size (tiny-text stuffing)
  - The same (or near-same) color as the page background (invisible text)
  - Rendered with PDF "invisible" render mode (Tr 3)
  - Positioned outside the visible page area (off-page stuffing)

Requires: pip install pymupdf --break-system-packages
"""

import fitz  # PyMuPDF
from dataclasses import dataclass, field


MIN_FONT_SIZE = 4.5          # pt — anything smaller is almost certainly stuffing
COLOR_SIMILARITY_THRESHOLD = 12  # max per-channel diff (0-255) to count as "matches background"
DEFAULT_BG = (255, 255, 255)     # assume white page unless we detect otherwise


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


def _int_color(color_val) -> tuple:
    """PyMuPDF span color is a packed int (sRGB). Unpack to (r,g,b) 0-255."""
    if isinstance(color_val, tuple):
        return color_val
    r = (color_val >> 16) & 255
    g = (color_val >> 8) & 255
    b = color_val & 255
    return (r, g, b)


def _color_matches_bg(color: tuple, bg: tuple = DEFAULT_BG) -> bool:
    return all(abs(c - b) <= COLOR_SIMILARITY_THRESHOLD for c, b in zip(color, bg))


def extract_clean_text(pdf_path: str) -> ExtractionResult:
    doc = fitz.open(pdf_path)
    clean_parts = []
    flagged = []

    for page in doc:
        page_rect = page.rect
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # 0 = text block
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
                    render_mode = span.get("flags", 0)  # bitfield; see note below

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


## ---------------------------------------------------------------------
## Section splitting
## ---------------------------------------------------------------------

import re
import json
import os

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "personal projects", "academic projects"],
    "education": ["education", "academic background", "qualifications"],
}

# Flatten to a lookup: normalized header text -> canonical section name
_HEADER_LOOKUP = {}
for canonical, variants in SECTION_HEADERS.items():
    for v in variants:
        _HEADER_LOOKUP[v] = canonical


def _looks_like_header(line: str) -> str | None:
    """Return the canonical section name if this line looks like a section header, else None."""
    normalized = line.strip().lower().strip(":").strip()
    if not normalized or len(normalized) > 40:
        return None
    return _HEADER_LOOKUP.get(normalized)


def split_into_sections(clean_text: str) -> dict:
    """
    Naive line-based section splitter. clean_text is assumed to still have
    original line breaks (join spans with '\n' instead of ' ' if you need this
    to work well -- see NOTE in extract_clean_text call site below).
    """
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


## ---------------------------------------------------------------------
## Skill extraction (vocabulary match against a shared skill list)
## ---------------------------------------------------------------------

# Starter vocabulary -- extend this with terms pulled from your actual JD + resumes.
# Share this exact list with Member 2 so keyword scoring uses the same normalized terms.
SKILL_VOCAB = [
    "python", "javascript", "java", "c++", "typescript", "sql", "node.js",
    "react", "express", "mongodb", "postgresql", "aws", "docker", "kubernetes",
    "git", "rest apis", "graphql", "html", "css", "django", "flask",
]


def extract_skills(text: str, vocab: list = SKILL_VOCAB) -> list:
    """Lowercase, punctuation-light substring match against the shared vocabulary."""
    normalized = re.sub(r"[^\w\s+.#-]", " ", text.lower())
    found = []
    for skill in vocab:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized):
            found.append(skill)
    return found


## ---------------------------------------------------------------------
## Full pipeline: PDF -> resume_<id>.json
## ---------------------------------------------------------------------

def build_resume_json(pdf_path: str, resume_id: str) -> dict:
    result = extract_clean_text(pdf_path)
    sections_raw = split_into_sections(result.clean_text)

    sections = {}
    for name, raw_text in sections_raw.items():
        sections[name] = {
            "raw_text": raw_text,
            "extracted_skills": extract_skills(raw_text) if name in ("skills", "experience", "projects") else [],
        }

    return {
        "resume_id": resume_id,
        "source_filename": os.path.basename(pdf_path),
        "sections": sections,
        "full_text_clean": result.clean_text,
        "integrity": {
            "hidden_spans_stripped": len(result.flagged_spans),
            "reasons": sorted(set(f.reason for f in result.flagged_spans)),
        },
    }


def process_batch(pdf_dir: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    for fname in sorted(os.listdir(pdf_dir)):
        if not fname.lower().endswith(".pdf"):
            continue
        resume_id = os.path.splitext(fname)[0]
        data = build_resume_json(os.path.join(pdf_dir, fname), resume_id)
        out_path = os.path.join(out_dir, f"{resume_id}.json")
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"wrote {out_path}  (stripped {data['integrity']['hidden_spans_stripped']} hidden span(s))")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1].lower().endswith(".pdf"):
        # single-file debug mode: prints the report + JSON
        result = extract_clean_text(sys.argv[1])
        print(result.report())
        data = build_resume_json(sys.argv[1], os.path.splitext(os.path.basename(sys.argv[1]))[0])
        print(json.dumps(data, indent=2))
    elif len(sys.argv) == 3:
        # batch mode: python hidden_text_strip.py <pdf_dir> <out_dir>
        process_batch(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  python hidden_text_strip.py <resume.pdf>            # single file, debug output")
        print("  python hidden_text_strip.py <pdf_dir> <out_dir>     # batch -> resume_<id>.json files")
        sys.exit(1)
