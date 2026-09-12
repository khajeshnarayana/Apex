"""
adapter.py — bridges Person 1's parser output into the matching engine.

WHY THIS EXISTS
    Person 1's JSON has three gaps the matching engine can't work around:
      1. extracted_skills is empty ([]) in every section
      2. .xml-sourced resumes have ALL sections blank (only full_text_clean)
      3. field names differ (resume_id vs candidate_id, no name field)

    Rather than block on Person 1 fixing their parser, we do skill detection
    ourselves here — from the raw text. Keyword matching is Person 2's job
    anyway, so this is the right place for it, and it means Person 1's parser
    can stay exactly as it is.

WHAT IT DOES
    Person 1 JSON  ->  adapter  ->  the shape matching.py already expects

Run standalone to inspect what it extracts:
    python adapter.py
"""

import json
import os
import re

from matching import SYNONYM_MAP


# ---------------------------------------------------------------------------
# Skill vocabulary
# ---------------------------------------------------------------------------
# Everything we know how to recognise in resume text. Built from the synonym
# map (so every JD skill and every alias is covered automatically), plus terms
# seen in this dataset that aren't in the map yet.

EXTRA_VOCABULARY = [
    # Languages
    "Java", "Python", "C++", "C#", "JavaScript", "TypeScript", "Dart", "Kotlin",
    "Swift", "Go", "Rust", "Ruby", "PHP", "Bash", "SQL", "R", "Scala",
    # Mobile
    "Flutter", "React Native", "Android SDK", "Android Studio", "Xcode",
    "Jetpack Compose", "SwiftUI",
    # Backend / frameworks
    "Spring Boot", "Spring", "Django", "Flask", "FastAPI", "Express", "NestJS",
    "Django REST Framework", "Node.js", "Laravel",
    # Frontend
    "React", "Vue", "Angular", "Next.js", "Redux", "HTML", "CSS", "Tailwind",
    "Bootstrap", "jQuery",
    # Data / ML
    "Pandas", "NumPy", "Scrapy", "TensorFlow", "PyTorch", "scikit-learn",
    "Matplotlib", "Jupyter", "Machine Learning", "Deep Learning", "NLP",
    # Databases
    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis", "Firebase",
    "Firestore", "DynamoDB", "Oracle",
    # Infra / tools
    "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "Jenkins", "Linux",
    "AWS", "Azure", "GCP", "Celery", "RabbitMQ", "Kafka", "Nginx",
    "Postman", "Play Console", "Provider",
    # API / architecture
    "REST API", "REST APIs", "RESTful API", "GraphQL", "Microservices",
    "JWT", "OAuth",
    # Testing / process
    "JUnit", "PyTest", "Jest", "Selenium", "Agile", "Scrum",
    "Unit Testing", "Integration Testing",
    # CS fundamentals (often in a Concepts: line)
    "Data Structures", "Algorithms", "OOP", "System Design", "Multithreading",
    "DBMS", "Operating Systems", "Computer Networks",
]


def build_vocabulary():
    """Every term we can recognise: synonym map keys + aliases + extras."""
    vocab = set()
    for canonical, aliases in SYNONYM_MAP.items():
        vocab.add(canonical)
        vocab.update(aliases)
    vocab.update(EXTRA_VOCABULARY)
    # Longest first, so "React Native" is matched before bare "React"
    return sorted(vocab, key=len, reverse=True)


VOCABULARY = build_vocabulary()


def extract_skills_from_text(text):
    """
    Find every known skill term present in a chunk of text.

    Uses word-boundary regex so 'Go' doesn't match inside 'Google' and
    'R' doesn't match every capital R in the document. Terms containing
    regex-special characters (C++, Node.js, .NET) are escaped.
    """
    if not text:
        return []

    found = []
    for term in VOCABULARY:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(term)

    # Drop a term if it's a substring of a longer term we already matched,
    # e.g. keep "React Native", drop the bare "React" it contains.
    deduped = []
    for term in found:
        if not any(term != other and term.lower() in other.lower() for other in found):
            deduped.append(term)

    return deduped


# ---------------------------------------------------------------------------
# Name extraction
# ---------------------------------------------------------------------------

def extract_name(resume_json):
    """
    Person 1's JSON has no name field, so derive one.
    First line of full_text_clean is the candidate's name in this dataset.
    Falls back to prettifying resume_id.
    """
    full_text = resume_json.get("full_text_clean", "").strip()
    if full_text:
        first_line = full_text.split("\n")[0].strip()
        # Sanity check: a name is short and has no digits or @
        if first_line and len(first_line) < 50 and not re.search(r"[\d@|]", first_line):
            return first_line.title()

    # Fallback: App_Developer_Resume_1_Siddharth_Rao -> Siddharth Rao
    resume_id = resume_json.get("resume_id", "")
    parts = resume_id.split("_")
    name_parts = [p for p in parts if p and p[0].isupper() and not p.isdigit()]
    trailing = name_parts[-2:] if len(name_parts) >= 2 else name_parts
    return " ".join(trailing) if trailing else resume_id


# ---------------------------------------------------------------------------
# The adapter
# ---------------------------------------------------------------------------

def adapt(resume_json):
    """
    Convert one of Person 1's resume JSON objects into the shape
    matching.py expects.

    Handles the empty-section case: when a resume has no populated sections
    (the .xml-sourced ones), everything falls back to full_text_clean and
    the detected skills land under 'full_text', which carries a middling
    section weight since we can't tell whether a skill was demonstrated in
    a project or merely listed.
    """
    sections_in = resume_json.get("sections", {})

    def raw(section_name):
        section = sections_in.get(section_name, {})
        if isinstance(section, dict):
            return (section.get("raw_text") or "").strip()
        return str(section or "").strip()

    skills_text = raw("skills")
    experience_text = raw("experience")
    projects_text = raw("projects")
    summary_text = raw("summary")
    education_text = raw("education")

    sections_populated = any([skills_text, experience_text, projects_text])
    full_text = resume_json.get("full_text_clean", "").strip()

    if sections_populated:
        extracted = {
            "skills_section": extract_skills_from_text(skills_text),
            "experience": extract_skills_from_text(experience_text),
            "projects": extract_skills_from_text(projects_text),
        }
        sections_out = {
            "skills": skills_text,
            "experience": experience_text,
            "projects": projects_text,
            "education": education_text,
            "summary": summary_text,
        }
    else:
        # Parsing gave us nothing structured — fall back to the whole document.
        extracted = {
            "skills_section": [],
            "experience": [],
            "projects": [],
            "full_text": extract_skills_from_text(full_text),
        }
        sections_out = {
            "skills": "",
            "experience": full_text,
            "projects": "",
            "education": "",
            "summary": "",
        }

    return {
        "candidate_id": resume_json.get("resume_id", "unknown"),
        "name": extract_name(resume_json),
        "sections": sections_out,
        "extracted_skills": extracted,
        "_parse_quality": "sectioned" if sections_populated else "fulltext_fallback",
    }


def load_resumes(directory):
    """Load and adapt every .json file in a directory."""
    adapted = []
    for filename in sorted(os.listdir(directory)):
        if not filename.lower().endswith(".json"):
            continue
        path = os.path.join(directory, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                adapted.append(adapt(json.load(f)))
        except Exception as e:
            print(f"  !! skipped {filename}: {e}")
    return adapted


# ---------------------------------------------------------------------------
# Inspect what the adapter pulls out
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    PARSED_DIR = r"D:\DEV\Apex\data\parsed"   # <-- point this at Person 1's output

    if not os.path.isdir(PARSED_DIR):
        print(f"Directory not found: {PARSED_DIR}")
        print("Edit PARSED_DIR at the bottom of this file to wherever")
        print("Person 1's .json files actually are.")
        raise SystemExit(1)

    resumes = load_resumes(PARSED_DIR)
    print(f"\nAdapted {len(resumes)} resumes.\n")

    for r in resumes:
        print("=" * 68)
        print(f"{r['name']}   ({r['candidate_id']})")
        print(f"parse quality: {r['_parse_quality']}")
        for section, skills in r["extracted_skills"].items():
            if skills:
                print(f"   {section}: {', '.join(skills)}")
        if not any(r["extracted_skills"].values()):
            print("   !! NO SKILLS DETECTED — investigate this one")
        print()