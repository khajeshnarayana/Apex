"""
test_real_resumes.py — score REAL resumes from the dataset against a plausible JD.

Purpose: check that ranking spread is sensible BEFORE the real JD drops.
Expectation:
    - SDE / Python Dev should rank high on a backend-ish JD
    - App Dev should land mid
    - Sales / Video Editing should sink to near-zero

If Sales scores anywhere near the developers, the weights need work.

Run:  python test_real_resumes.py
"""

from matching import rank_candidates

# ---------------------------------------------------------------------------
# Placeholder JD — the REAL Sample_JD drops at 1-2pm, swap it in then.
# This one is modelled on the problem statement's "Junior Full Stack
# Developer Intern" description so the test is at least realistic.
# ---------------------------------------------------------------------------

PLACEHOLDER_JD = {
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


# ---------------------------------------------------------------------------
# Real resume data, transcribed from the actual .docx files in the dataset.
# Skills are split by the section they appeared in, matching Person 1's schema.
# ---------------------------------------------------------------------------

REAL_RESUMES = [
    {
        "candidate_id": "SDE_Resume_1",
        "name": "Aditya Joshi",
        "sections": {
            "skills": (
                "Languages: Java, Python, C++, SQL. "
                "Concepts: Data Structures & Algorithms, OOP, System Design, Multithreading. "
                "Frameworks & Tools: Spring Boot, REST APIs, JUnit, Git, GitHub. "
                "Databases & Platforms: MySQL, MongoDB, Docker, Linux, AWS (basic)."
            ),
            "experience": (
                "Software Engineering Intern. Designed and implemented backend "
                "microservices using Spring Boot, serving 10,000+ daily requests. "
                "Wrote unit and integration tests improving code coverage from 60% to 85%. "
                "Participated in code reviews and sprint planning following Agile methodology."
            ),
            "projects": (
                "Distributed Task Scheduler using Java, Spring Boot, MySQL, RabbitMQ. "
                "Designed a distributed task scheduling system supporting retries and "
                "priority queues. Library Management REST API using Java, Spring Boot, "
                "MySQL. Built a RESTful API with JWT authentication and role-based access "
                "control. Wrote comprehensive JUnit test suites. Competitive Programming "
                "Portfolio in C++, solved 600+ problems on Codeforces and LeetCode."
            ),
            "education": "B.Tech Computer Science & Engineering, CGPA 9.2",
        },
        "extracted_skills": {
            "skills_section": [
                "Java", "Python", "C++", "SQL", "Spring Boot", "REST APIs",
                "JUnit", "Git", "GitHub", "MySQL", "MongoDB", "Docker", "Linux", "AWS",
            ],
            "experience": ["Spring Boot", "Agile", "Microservices"],
            "projects": [
                "Java", "Spring Boot", "MySQL", "RabbitMQ", "RESTful API", "JUnit", "C++",
            ],
        },
    },
    {
        "candidate_id": "Python_Resume_1",
        "name": "Karan Malhotra",
        "sections": {
            "skills": (
                "Languages: Python, SQL, Bash. "
                "Frameworks: Django, Flask, FastAPI. "
                "Data & Tools: Pandas, NumPy, Celery, Redis. "
                "DevOps & Platforms: Git, GitHub, Docker, Linux, PostgreSQL, MySQL, REST APIs."
            ),
            "experience": (
                "Python Developer Intern. Developed and maintained REST APIs using "
                "Django REST Framework for an internal reporting tool. Wrote automation "
                "scripts that reduced manual data-entry workload by 40%. Optimised "
                "PostgreSQL queries, improving average response time by 25%."
            ),
            "projects": (
                "Inventory Management System using Python, Django, PostgreSQL. Built a "
                "multi-user inventory system with role-based dashboards. Designed "
                "normalized database schema. Implemented automated email notifications "
                "using Celery and Redis. Web Scraping & Data Pipeline using Python, "
                "Scrapy, Pandas, PostgreSQL. URL Shortener API using Python, FastAPI, "
                "Redis, handling 1,000+ requests per minute."
            ),
            "education": "B.Tech Computer Science & Engineering, CGPA 9.0",
        },
        "extracted_skills": {
            "skills_section": [
                "Python", "SQL", "Bash", "Django", "Flask", "FastAPI", "Pandas",
                "NumPy", "Celery", "Redis", "Git", "GitHub", "Docker", "Linux",
                "PostgreSQL", "MySQL", "REST APIs",
            ],
            "experience": ["Django REST Framework", "REST APIs", "PostgreSQL"],
            "projects": [
                "Python", "Django", "PostgreSQL", "Celery", "Redis", "Scrapy",
                "Pandas", "FastAPI",
            ],
        },
    },
    {
        "candidate_id": "App_Resume_1",
        "name": "Siddharth Rao",
        "sections": {
            "skills": (
                "Languages: Dart, Kotlin, JavaScript, Python. "
                "Frameworks: Flutter, React Native, Android SDK. "
                "Backend & Tools: Firebase, REST APIs, SQLite, Git, GitHub. "
                "Platforms: Android Studio, Xcode (basic), Play Console, Postman."
            ),
            "experience": (
                "Mobile App Development Intern. Developed UI screens and state "
                "management logic for a Flutter-based internal field-reporting app. "
                "Integrated Firebase Authentication and Firestore, reducing backend "
                "setup time by 50%. Fixed 25+ UI and performance bugs."
            ),
            "projects": (
                "Campus Event Management App using Flutter and Firebase. Built a "
                "cross-platform app for event discovery, RSVP, and push notifications. "
                "Used Firestore for real-time updates. Personal Finance Tracker App "
                "using Flutter, SQLite, Provider. Fitness Tracking App using React "
                "Native and Firebase, syncing data using Firebase Realtime Database."
            ),
            "education": "B.Tech Information Technology, CGPA 8.4",
        },
        "extracted_skills": {
            "skills_section": [
                "Dart", "Kotlin", "JavaScript", "Python", "Flutter", "React Native",
                "Android SDK", "Firebase", "REST APIs", "SQLite", "Git", "GitHub",
                "Android Studio", "Postman",
            ],
            "experience": ["Flutter", "Firebase", "Firestore"],
            "projects": [
                "Flutter", "Firebase", "Firestore", "SQLite", "React Native",
            ],
        },
    },
    {
        "candidate_id": "Sales_Resume_1",
        "name": "Sahil Khanna",
        "sections": {
            "skills": (
                "Core Skills: Lead Generation, Cold Outreach, Negotiation, Client "
                "Relationship Management. Tools: CRM (HubSpot/Salesforce basics), "
                "LinkedIn Sales Navigator, Excel. Other: Pitch Deck Creation, Market "
                "Research, Objection Handling. Soft Skills: Communication, Persistence."
            ),
            "experience": (
                "Sales Intern. Generated 150+ qualified leads through cold outreach, "
                "contributing to 12 closed deals. Conducted product demos for "
                "prospective clients, achieving a 35% demo-to-trial conversion rate. "
                "Maintained CRM records and follow-up cadences."
            ),
            "projects": (
                "Campus Ambassador Sales Drive using HubSpot and Excel, achieving 200+ "
                "sign-ups. Built a referral incentive structure. B2B Outreach Simulation "
                "Project using LinkedIn Sales Navigator and Excel. Local Business "
                "Partnership Drive involving cold calling and Google Sheets."
            ),
            "education": "Bachelor of Business Administration, CGPA 8.2",
        },
        "extracted_skills": {
            "skills_section": [
                "Lead Generation", "Cold Outreach", "Negotiation", "CRM", "HubSpot",
                "Salesforce", "LinkedIn Sales Navigator", "Excel", "Market Research",
            ],
            "experience": ["CRM", "Cold Outreach"],
            "projects": ["HubSpot", "Excel", "LinkedIn Sales Navigator"],
        },
    },
    {
        "candidate_id": "Video_Resume_1",
        "name": "Rahul Saxena",
        "sections": {
            "skills": (
                "Editing Software: Adobe Premiere Pro, After Effects, DaVinci Resolve, "
                "CapCut. Skills: Color Grading, Motion Graphics, Sound Design, "
                "Storyboarding. Other Tools: Photoshop, Canva, Audacity. "
                "Formats: Reels/Shorts, YouTube Long-form, Promotional Videos."
            ),
            "experience": (
                "Video Editing Intern. Edited 30+ short-form videos for social "
                "campaigns, increasing average watch-through rate by 25%. Created "
                "motion graphics templates in After Effects, cutting future editing "
                "time by 30%. Collaborated with the marketing team on brand guidelines."
            ),
            "projects": (
                "College Fest Highlight Reel edited in Premiere Pro and After Effects, "
                "viewed 15,000+ times online. YouTube Channel Editing Series using "
                "Premiere Pro and DaVinci Resolve, editing 20+ episodes. Short Film "
                "Project edited in Premiere Pro and Audacity, handling pacing, sound "
                "mixing, and color correction."
            ),
            "education": "B.A. Film, Television and New Media Production, CGPA 8.7",
        },
        "extracted_skills": {
            "skills_section": [
                "Adobe Premiere Pro", "After Effects", "DaVinci Resolve", "CapCut",
                "Color Grading", "Motion Graphics", "Sound Design", "Photoshop",
                "Canva", "Audacity",
            ],
            "experience": ["After Effects", "Motion Graphics"],
            "projects": ["Premiere Pro", "After Effects", "DaVinci Resolve", "Audacity"],
        },
    },
]


if __name__ == "__main__":
    print("\n" + "=" * 72)
    print("RANKING REAL DATASET RESUMES AGAINST A PLACEHOLDER FULL-STACK JD")
    print("=" * 72)
    print("\nSANITY CHECK — what we EXPECT to see:")
    print("  * Developers (SDE / Python / App) should cluster at the top")
    print("  * Sales and Video Editing should sink clearly to the bottom")
    print("  * There should be visible GAPS between tiers, not a tight cluster")
    print("\nIf Sales/Video score close to the developers, the weights need work.\n")

    ranked = rank_candidates(PLACEHOLDER_JD, REAL_RESUMES)

    for i, r in enumerate(ranked, 1):
        print(f"\n#{i}  {r['name']}  ({r['candidate_id']})")
        print(f"     FINAL: {r['final_score']}   |   keyword: {r['keyword_score']}   semantic: {r['semantic_score']}")

        if r["matched_skills"]:
            print("     matched:")
            for m in r["matched_skills"]:
                tag = m["match_type"]
                extra = f"  <- found as '{m['found_as']}'" if tag == "synonym" else ""
                print(f"        + {m['skill']} [{tag}]{extra}")
        else:
            print("     matched: (none)")

        if r["missing_required_skills"]:
            print("     missing:")
            for m in r["missing_required_skills"]:
                hint = "  (but resume reads as related)" if m["semantic_hint"] else ""
                print(f"        - {m['skill']}{hint}")

    # Spread check — the thing judges will notice
    scores = [r["final_score"] for r in ranked]
    print("\n" + "-" * 72)
    print(f"SPREAD CHECK:  top={max(scores)}  bottom={min(scores)}  range={round(max(scores) - min(scores), 4)}")
    print("A healthy range here is roughly 0.3+. A tight cluster means poor differentiation.")
    print("-" * 72 + "\n")