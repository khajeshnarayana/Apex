"""
matching.py — Person 2's core: keyword + semantic matching, fused into a final score.

Expects resume data in this shape (from Person 1):
{
    "candidate_id": "resume_03",
    "name": "Jane Doe",
    "sections": {
        "skills": "React, MongoDB, ...",
        "experience": "Built REST APIs with Express and MongoDB...",
        "projects": "...",
        "education": "..."
    },
    "extracted_skills": {
        "skills_section": ["React", "MongoDB"],
        "experience": ["Node.js"],
        "projects": ["React", "MongoDB", "REST API"]
    }
}

Expects JD data in this shape:
{
    "full_text": "We are looking for a Junior Full Stack Developer...",
    "required_skills": ["React", "Node.js", "MongoDB", "Docker"],
    "nice_to_have_skills": ["AWS", "TypeScript"]
}

Outputs a ranked list of:
{
    "candidate_id": ..., "name": ...,
    "final_score": 0.0-1.0,
    "keyword_score": 0.0-1.0,
    "semantic_score": 0.0-1.0,
    "matched_skills": [...],
    "missing_required_skills": [...]
}
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# ---------------------------------------------------------------------------
# Config — tune these after eyeballing results on the real 18 resumes
# ---------------------------------------------------------------------------

KEYWORD_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6

# Section weighting for skill matches — a skill backed by a project/experience
# counts more than one just listed in a skills dump.
SECTION_WEIGHTS = {
    # Skill demonstrated in real work — strongest evidence.
    "projects": 1.0,
    "experience": 1.0,
    # Skill claimed in a list, not shown in use.
    "skills_section": 0.6,
    # Weak evidence. A course title like "Programming Foundations with
    # JavaScript, HTML and CSS" mentions three skills but demonstrates none.
    "certifications": 0.4,
    # Weakest. Achievements and extracurriculars name a lot of tools in
    # passing (club events, CTF write-ups, blog posts) without showing
    # the candidate actually built anything with them.
    "achievements": 0.3,
    # Used when section parsing failed entirely and we only have the whole
    # document. We can't tell whether a skill was demonstrated in a project
    # or merely listed, so this sits between the two — neither rewarding nor
    # penalising a candidate for their resume's file format.
    "full_text": 0.8,
}

# Semantic score above which a "missing" skill gets flagged as possibly
# covered anyway — resume seems related in meaning even without the keyword.
SEMANTIC_FLAG_THRESHOLD = 0.45

# How far apart the two signals must be before we flag the disagreement.
# A large gap means the two methods are "seeing" different things about the
# same candidate, which is worth a human second look either way.
SIGNAL_DISAGREEMENT_THRESHOLD = 0.30
# Skill synonym map — catches "Express implies Node.js" type cases.
# Extend this list based on the actual JD + resumes you're given.
SYNONYM_MAP = {
    # Backend / server frameworks
    "Node.js": ["Express", "Express.js", "NestJS", "Node", "Koa", "Koa.js"],
    "Python backend": ["Flask", "Django", "FastAPI", "Django REST Framework", "DRF"],
    "Java backend": ["Spring", "Spring Boot", "Spring MVC", "Hibernate"],
    ".NET": [".NET Core", "ASP.NET", "C#", "ASP.NET Core"],
    "PHP": ["Laravel", "Symfony", "CodeIgniter"],
    "Ruby": ["Ruby on Rails", "Rails"],

    # Frontend frameworks / libraries
    "React": ["React.js", "ReactJS", "Next.js", "NextJS", "Redux", "React Native"],
    "Vue": ["Vue.js", "VueJS", "Nuxt.js", "Nuxt"],
    "Angular": ["AngularJS", "Angular.js"],
    "Frontend": ["React", "Vue", "Angular", "Svelte", "jQuery"],
    "CSS": ["Tailwind", "Tailwind CSS", "Bootstrap", "SCSS", "Sass", "Styled Components"],
    "JavaScript": ["JS", "ES6", "ECMAScript", "TypeScript", "TS"],

    # Databases
    "SQL": ["MySQL", "PostgreSQL", "Postgres", "SQLite", "MariaDB", "MS SQL", "SQL Server"],
    "NoSQL": ["MongoDB", "Firebase", "Firestore", "DynamoDB", "Cassandra", "CouchDB"],
    "MongoDB": ["Mongo", "Mongoose"],
    "Database": ["SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL"],

    # API / architecture
    "REST API": ["REST", "RESTful API", "REST APIs", "RESTful", "API development"],
    "GraphQL": ["Apollo", "Apollo Client", "Apollo Server"],
    "Microservices": ["Microservice architecture", "Service-oriented architecture", "SOA"],

    # DevOps / cloud
    "Docker": ["Containerization", "Containers", "Docker Compose"],
    "Kubernetes": ["K8s", "EKS", "GKE", "AKS"],
    "CI/CD": ["Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Continuous Integration", "Continuous Deployment"],
    "AWS": ["Amazon Web Services", "EC2", "S3", "Lambda", "AWS Lambda", "CloudFront", "RDS"],
    "Azure": ["Microsoft Azure"],
    "GCP": ["Google Cloud", "Google Cloud Platform"],
    "Cloud": ["AWS", "Azure", "GCP", "Google Cloud"],

    # Version control / tools
    "Git": ["GitHub", "GitLab", "Bitbucket", "version control"],
    "Testing": ["Jest", "Mocha", "Chai", "PyTest", "Unit testing", "JUnit", "Selenium"],

    # General / soft-mapped terms
    "Full Stack": ["MERN", "MEAN", "MEVN", "Full-Stack Development"],
    "Agile": ["Scrum", "Kanban", "Sprint planning"],
}

_model = None


def get_model():
    """Lazy-load the locally cached embedding model once."""
    global _model
    if _model is None:
        # Document analysis is intentionally offline. If this model has not
        # already been installed/cached, fail clearly instead of downloading it.
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            local_files_only=True,
        )
    return _model


# ---------------------------------------------------------------------------
# Keyword / skill-based scoring
# ---------------------------------------------------------------------------

def _find_evidence(term, section_text, max_len=180):
    """
    Pull the sentence from a resume section where a matched skill actually
    appears — so an explanation can show proof, not just a claim.

    Splits on sentence-ish boundaries (periods, newlines, bullets) and returns
    the first fragment containing the term, trimmed to a readable length.
    Returns None if nothing suitable is found.
    """
    if not section_text or not term:
        return None

    # Resume text uses periods, newlines, and bullet characters as separators.
    fragments = re.split(r"(?<=\.)\s+|\n+|(?:^|\s)[-•*]\s+", section_text)

    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"

    best = None
    for frag in fragments:
        frag = " ".join(frag.split())  # collapse whitespace
        if not frag or len(frag) < 12:
            continue
        if re.search(pattern, frag, flags=re.IGNORECASE):
            # Prefer a fragment that reads like a real sentence over a bare
            # comma-separated skills list, which proves much less.
            looks_like_prose = len(frag.split()) >= 6 and frag.count(",") < 5
            if looks_like_prose:
                best = frag
                break
            if best is None:
                best = frag

    if not best:
        return None

    if len(best) > max_len:
        best = best[:max_len].rsplit(" ", 1)[0] + "..."
    return best


def _skill_matches(required_skill, resume_skills_by_section, section_texts=None):
    """
    Check if a required skill (or one of its synonyms) appears in the resume.

    Returns the best section weight it was found under, which term matched,
    whether that was an exact or synonym match, which section it came from,
    and — when section_texts is supplied — the sentence proving it.
    """
    candidates = [required_skill] + SYNONYM_MAP.get(required_skill, [])
    best_weight = 0.0
    matched_term = None
    match_type = None
    found_in = None

    for section, weight in SECTION_WEIGHTS.items():
        skills_in_section = resume_skills_by_section.get(section, [])
        for cand in candidates:
            for found_skill in skills_in_section:
                if cand.lower() == found_skill.lower():
                    if weight > best_weight:
                        best_weight = weight
                        matched_term = found_skill
                        match_type = (
                            "exact" if cand.lower() == required_skill.lower()
                            else "synonym"
                        )
                        found_in = section

    evidence = None
    if matched_term and section_texts:
        # Look in the section it scored from first, then anywhere else.
        search_order = [found_in] + [s for s in section_texts if s != found_in]
        for section in search_order:
            evidence = _find_evidence(matched_term, section_texts.get(section, ""))
            if evidence:
                break

    return best_weight, matched_term, match_type, found_in, evidence


def keyword_score(jd_data, resume_data):
    """
    Score = weighted fraction of required skills found (section-weighted),
    plus a smaller bonus for nice-to-have skills found.

    Returns (score, matched_skills_list, missing_required_list) where
    matched_skills_list is a list of dicts:
        {
          "skill": "Node.js",
          "found_as": "Express",
          "match_type": "synonym",
          "found_in": "projects",
          "evidence": "Built backend services using Express and Mongoose...",
          "required": True
        }
    and missing_required_list is a plain list of skill name strings.
    """
    required = jd_data.get("required_skills", [])
    nice_to_have = jd_data.get("nice_to_have_skills", [])
    resume_skills = resume_data.get("extracted_skills", {})

    # Map the engine's section keys onto the raw text we can quote from.
    sections = resume_data.get("sections", {})
    section_texts = {
        "skills_section": sections.get("skills", ""),
        "experience": sections.get("experience", ""),
        "projects": sections.get("projects", ""),
        "certifications": sections.get("certifications", ""),
        "achievements": sections.get("achievements", ""),
        "full_text": sections.get("experience", ""),  # fallback stores text here
    }

    matched = []
    missing = []
    required_weight_sum = 0.0

    for skill in required:
        weight, term, match_type, found_in, evidence = _skill_matches(
            skill, resume_skills, section_texts
        )
        required_weight_sum += weight
        if weight > 0:
            matched.append({
                "skill": skill,
                "found_as": term,
                "match_type": match_type,
                "found_in": found_in,
                "evidence": evidence,
                "required": True,
            })
        else:
            missing.append(skill)

    required_score = required_weight_sum / len(required) if required else 0.0

    nice_weight_sum = 0.0
    for skill in nice_to_have:
        weight, term, match_type, found_in, evidence = _skill_matches(
            skill, resume_skills, section_texts
        )
        nice_weight_sum += weight
        if weight > 0:
            matched.append({
                "skill": skill,
                "found_as": term,
                "match_type": match_type,
                "found_in": found_in,
                "evidence": evidence,
                "required": False,
            })

    nice_score = nice_weight_sum / len(nice_to_have) if nice_to_have else 0.0

    # Required skills matter far more than nice-to-haves
    final_keyword_score = 0.85 * required_score + 0.15 * nice_score

    return round(final_keyword_score, 4), matched, missing


# ---------------------------------------------------------------------------
# Semantic scoring
# ---------------------------------------------------------------------------

def _resume_text_for_embedding(resume_data):
    """Prioritize Experience + Projects text over Education/contact info."""
    sections = resume_data.get("sections", {})
    parts = [
        sections.get("experience", ""),
        sections.get("projects", ""),
        sections.get("skills", ""),
    ]
    text = " ".join(p for p in parts if p).strip()
    return text if text else resume_data.get("sections", {}).get("full_text", "")


def semantic_scores_batch(jd_data, resumes):
    """
    Compute semantic similarity for ALL resumes at once (much faster than
    one-by-one since the model batches embeddings).
    Returns a list of scores aligned with `resumes`.
    """
    model = get_model()
    jd_text = jd_data.get("full_text", "")
    resume_texts = [_resume_text_for_embedding(r) for r in resumes]

    jd_embedding = model.encode([jd_text])
    resume_embeddings = model.encode(resume_texts)

    sims = cosine_similarity(jd_embedding, resume_embeddings)[0]
    # cosine similarity is already 0-1-ish for normalized sentence embeddings;
    # clip just in case of tiny negative float noise
    return [round(float(max(0.0, s)), 4) for s in sims]


# ---------------------------------------------------------------------------
# Fusion + ranking
# ---------------------------------------------------------------------------

def rank_candidates(jd_data, resumes):
    """
    Main entry point. Takes JD data + list of resume data dicts,
    returns a ranked list (highest final_score first).
    """
    sem_scores = semantic_scores_batch(jd_data, resumes)

    results = []
    for resume_data, sem_score in zip(resumes, sem_scores):
        kw_score, matched, missing = keyword_score(jd_data, resume_data)
        final = round(KEYWORD_WEIGHT * kw_score + SEMANTIC_WEIGHT * sem_score, 4)

        # For skills that weren't keyword/synonym matched, flag whether the
        # resume still seems semantically related overall — gives Person 3
        # a nuance to mention in explanations ("not explicitly listed, but
        # resume content suggests related experience").
        semantic_hint = sem_score >= SEMANTIC_FLAG_THRESHOLD
        missing_detailed = [
            {"skill": skill, "semantic_hint": semantic_hint}
            for skill in missing
        ]

        # When the two signals disagree sharply, that itself is information a
        # recruiter can act on — it usually means the resume describes relevant
        # work in vocabulary the JD doesn't use, or conversely that it lists the
        # right buzzwords without describing matching work.
        gap = sem_score - kw_score
        if gap >= SIGNAL_DISAGREEMENT_THRESHOLD:
            signal_note = "semantic_above_keyword"
        elif gap <= -SIGNAL_DISAGREEMENT_THRESHOLD:
            signal_note = "keyword_above_semantic"
        else:
            signal_note = None

        results.append({
            "candidate_id": resume_data.get("candidate_id"),
            "name": resume_data.get("name"),
            "final_score": final,
            "keyword_score": kw_score,
            "semantic_score": sem_score,
            "matched_skills": matched,
            "missing_required_skills": missing_detailed,
            "signal_note": signal_note,
        })

    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Quick manual test with fake data — run: python matching.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fake_jd = {
        "full_text": (
            "We are looking for a Junior Full Stack Developer Intern. "
            "Must have experience with React, Node.js, MongoDB, and REST APIs. "
            "Docker knowledge is required. AWS and TypeScript are a plus."
        ),
        "required_skills": ["React", "Node.js", "MongoDB", "REST API", "Docker"],
        "nice_to_have_skills": ["AWS", "TypeScript"],
    }

    fake_resumes = [
        {
            "candidate_id": "resume_01",
            "name": "Jane Doe",
            "sections": {
                "experience": "Built REST APIs with Express and MongoDB for an e-commerce platform.",
                "projects": "Full stack app using React frontend and Node.js backend, deployed with Docker.",
                "skills": "React, MongoDB, Docker, AWS",
            },
            "extracted_skills": {
                "skills_section": ["React", "MongoDB", "Docker", "AWS"],
                "experience": ["Express", "MongoDB", "REST API"],
                "projects": ["React", "Node.js", "Docker"],
            },
        },
        {
            "candidate_id": "resume_02",
            "name": "Raj Kumar",
            "sections": {
                "experience": "Worked on internal tools using React.",
                "projects": "Simple portfolio website with React.",
                "skills": "React, HTML, CSS",
            },
            "extracted_skills": {
                "skills_section": ["React", "HTML", "CSS"],
                "experience": ["React"],
                "projects": ["React"],
            },
        },
        {
            "candidate_id": "resume_03",
            "name": "Amy Chen",
            "sections": {
                "experience": "Data analysis using Python and Excel.",
                "projects": "Machine learning model for sales prediction.",
                "skills": "Python, Pandas, Excel",
            },
            "extracted_skills": {
                "skills_section": ["Python", "Pandas", "Excel"],
                "experience": [],
                "projects": ["Python"],
            },
        },
        # --- Harder edge cases below ---
        {
            # Never writes the literal JD words — only synonym/equivalent terms.
            # Should trigger [synonym] tags across the board, not [exact].
            "candidate_id": "resume_04",
            "name": "Priya Sharma",
            "sections": {
                "experience": (
                    "Built backend services using Express and Mongoose for a food "
                    "delivery app, exposing RESTful APIs consumed by the frontend."
                ),
                "projects": (
                    "Deployed the application using Docker Compose across "
                    "development and staging environments."
                ),
                "skills": "Express, Mongoose, RESTful API, Docker Compose, React.js",
            },
            "extracted_skills": {
                "skills_section": ["Express", "Mongoose", "RESTful API", "Docker Compose", "React.js"],
                "experience": ["Express", "Mongoose", "RESTful API"],
                "projects": ["Docker Compose"],
            },
        },
        {
            # Skill list is nearly empty (bad parsing / no explicit skills section),
            # but the written experience text is clearly related in meaning.
            # Should trigger semantic_hint=True on missing skills.
            "candidate_id": "resume_05",
            "name": "Karan Mehta",
            "sections": {
                "experience": (
                    "Developed and deployed a full stack web application end to end: "
                    "designed the frontend UI, built backend APIs, connected them to a "
                    "database, and containerized the whole system for deployment."
                ),
                "projects": (
                    "Led a college project building a complete web platform from "
                    "frontend to backend, including database design and deployment."
                ),
                "skills": "",
            },
            "extracted_skills": {
                "skills_section": [],
                "experience": [],
                "projects": [],
            },
        },
        {
            # Skill listed ONLY in the skills section, never used in a project or
            # experience bullet — tests that section-weighting actually lowers
            # the contribution vs a skill backed by real usage.
            "candidate_id": "resume_06",
            "name": "Sara Ahmed",
            "sections": {
                "experience": "Customer support intern, handled client queries.",
                "projects": "",
                "skills": "React, Node.js, MongoDB, Docker, AWS, REST API",
            },
            "extracted_skills": {
                "skills_section": ["React", "Node.js", "MongoDB", "Docker", "AWS", "REST API"],
                "experience": [],
                "projects": [],
            },
        },
    ]

    ranked = rank_candidates(fake_jd, fake_resumes)
    for i, r in enumerate(ranked, 1):
        print(f"\n#{i} {r['name']} (final: {r['final_score']})")
        print(f"   keyword: {r['keyword_score']}  semantic: {r['semantic_score']}")

        print("   matched:")
        for m in r["matched_skills"]:
            tag = m["match_type"]
            extra = f" (found as '{m['found_as']}')" if tag == "synonym" else ""
            print(f"      - {m['skill']} [{tag}]{extra}")

        print("   missing:")
        for m in r["missing_required_skills"]:
            hint = " (resume seems related overall despite no keyword hit)" if m["semantic_hint"] else ""
            print(f"      - {m['skill']}{hint}")
