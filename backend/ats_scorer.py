# ============================================
# AI Career Navigator — ats_scorer.py
# Calculates how well a resume matches a job
# description using NLP-like techniques
# No AI needed — pure Python logic
# ============================================

import re
from collections import Counter


# ── TECH SKILLS DICTIONARY ────────────────────────────────────────
# These are weighted higher because they're the most important
# keywords ATS systems look for

TECH_SKILLS = {
    # Programming languages
    "python", "javascript", "typescript", "java", "c++", "c#",
    "ruby", "go", "rust", "swift", "kotlin", "php", "scala",
    "r", "matlab", "bash", "shell", "perl",

    # Web frameworks
    "react", "angular", "vue", "nextjs", "nodejs", "express",
    "django", "fastapi", "flask", "spring", "rails", "laravel",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite",
    "dynamodb", "cassandra", "elasticsearch", "oracle",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "circleci", "ansible",

    # AI/ML
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "nlp", "computer vision",
    "llm", "openai", "langchain",

    # Tools & practices
    "git", "github", "jira", "agile", "scrum", "rest api",
    "graphql", "microservices", "ci/cd", "devops", "linux",

    # Data
    "tableau", "power bi", "spark", "hadoop", "kafka",
    "airflow", "dbt", "snowflake", "bigquery",
}

# Soft skills — weighted lower but still count
SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "problem solving",
    "analytical", "detail oriented", "collaborative", "innovative",
    "proactive", "adaptable", "organized", "creative",
    "critical thinking", "time management", "mentoring",
}

# Action verbs that ATS systems love
ACTION_VERBS = {
    "developed", "designed", "built", "implemented", "created",
    "managed", "led", "improved", "optimized", "delivered",
    "deployed", "architected", "engineered", "automated",
    "increased", "reduced", "launched", "collaborated",
    "analyzed", "streamlined", "mentored", "scaled",
}


# ── TEXT PROCESSING ────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Lowercase and remove special characters"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_words(text: str) -> list:
    """Split text into individual words"""
    return clean_text(text).split()

def extract_phrases(text: str, n: int = 2) -> list:
    """Extract n-word phrases (bigrams/trigrams)"""
    words = extract_words(text)
    phrases = []
    for i in range(len(words) - n + 1):
        phrases.append(" ".join(words[i:i+n]))
    return phrases

def extract_all_terms(text: str) -> set:
    """Extract all meaningful single words and phrases"""
    terms = set()
    cleaned = clean_text(text)

    # Single words
    terms.update(extract_words(cleaned))

    # 2-word phrases
    terms.update(extract_phrases(cleaned, 2))

    # 3-word phrases
    terms.update(extract_phrases(cleaned, 3))

    return terms


# ── KEYWORD EXTRACTION ─────────────────────────────────────────────

def extract_keywords(text: str) -> dict:
    """
    Extracts all meaningful keywords from text
    Returns a dict with keyword categories
    """
    terms = extract_all_terms(text)
    cleaned = clean_text(text)

    found_tech   = {s for s in TECH_SKILLS   if s in cleaned}
    found_soft   = {s for s in SOFT_SKILLS   if s in cleaned}
    found_action = {s for s in ACTION_VERBS  if s in cleaned}

    # Extract years of experience mentions
    exp_patterns = re.findall(
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)?',
        cleaned
    )
    experience_years = [int(y) for y in exp_patterns if int(y) < 50]

    # Extract education levels
    education = set()
    edu_keywords = {
        "bachelor", "master", "phd", "doctorate",
        "bs", "ms", "mba", "associate"
    }
    for edu in edu_keywords:
        if edu in cleaned:
            education.add(edu)

    return {
        "tech_skills":   found_tech,
        "soft_skills":   found_soft,
        "action_verbs":  found_action,
        "education":     education,
        "exp_years":     experience_years,
        "all_terms":     terms,
    }


# ── MAIN SCORING FUNCTION ──────────────────────────────────────────

def calculate_ats_score(
    resume_text: str,
    job_description: str
) -> dict:
    """
    Calculates ATS compatibility score between resume and job.

    Returns a dict with:
      - score: 0-100 float
      - breakdown: detailed scores per category
      - matched_keywords: what matched
      - missing_keywords: what's missing
      - suggestions: how to improve
    """

    # Extract keywords from both texts
    resume_kw = extract_keywords(resume_text)
    job_kw    = extract_keywords(job_description)

    # ── 1. TECH SKILLS SCORE (40% weight) ──
    job_tech    = job_kw["tech_skills"]
    resume_tech = resume_kw["tech_skills"]

    if job_tech:
        tech_matched = job_tech & resume_tech
        tech_score   = (len(tech_matched) / len(job_tech)) * 100
    else:
        tech_matched = set()
        tech_score   = 75.0  # no tech requirements = neutral

    # ── 2. KEYWORD OVERLAP SCORE (30% weight) ──
    # Compare all meaningful terms
    job_words    = job_kw["all_terms"]
    resume_words = resume_kw["all_terms"]

    # Filter to meaningful words (length > 3, not stopwords)
    stopwords = {
        "the", "and", "for", "with", "that", "this", "have",
        "from", "they", "will", "been", "their", "what", "when",
        "which", "more", "also", "your", "our", "you", "are",
        "was", "were", "has", "had", "not", "but", "can", "all"
    }

    meaningful_job = {
        w for w in job_words
        if len(w) > 3 and w not in stopwords
    }

    meaningful_resume = {
        w for w in resume_words
        if len(w) > 3 and w not in stopwords
    }

    if meaningful_job:
        keyword_matched = meaningful_job & meaningful_resume
        keyword_score   = min(
            (len(keyword_matched) / len(meaningful_job)) * 100,
            100
        )
    else:
        keyword_matched = set()
        keyword_score   = 50.0

    # ── 3. SOFT SKILLS SCORE (15% weight) ──
    job_soft    = job_kw["soft_skills"]
    resume_soft = resume_kw["soft_skills"]

    if job_soft:
        soft_matched = job_soft & resume_soft
        soft_score   = (len(soft_matched) / len(job_soft)) * 100
    else:
        soft_matched = set()
        soft_score   = 70.0

    # ── 4. ACTION VERBS SCORE (10% weight) ──
    resume_actions = resume_kw["action_verbs"]
    action_score   = min(len(resume_actions) * 10, 100)

    # ── 5. FORMAT/COMPLETENESS SCORE (5% weight) ──
    format_score = 0

    # Check for key resume sections
    resume_lower = resume_text.lower()
    sections = [
        "experience", "education", "skills",
        "projects", "summary", "objective"
    ]
    sections_found = sum(1 for s in sections if s in resume_lower)
    format_score += (sections_found / len(sections)) * 60

    # Check resume length (too short = bad)
    word_count = len(resume_text.split())
    if word_count >= 300:
        format_score += 40
    elif word_count >= 150:
        format_score += 20

    # ── WEIGHTED FINAL SCORE ──
    final_score = (
        tech_score    * 0.40 +
        keyword_score * 0.30 +
        soft_score    * 0.15 +
        action_score  * 0.10 +
        format_score  * 0.05
    )

    # Round to 1 decimal
    final_score = round(final_score, 1)

    # ── MISSING KEYWORDS ──
    missing_tech = job_tech - resume_tech
    missing_soft = job_soft - resume_soft

    # ── SUGGESTIONS ──
    suggestions = []

    if missing_tech:
        top_missing = list(missing_tech)[:5]
        suggestions.append(
            f"Add these technical skills if you have them: "
            f"{', '.join(top_missing)}"
        )

    if missing_soft:
        suggestions.append(
            f"Consider mentioning: {', '.join(list(missing_soft)[:3])}"
        )

    if action_score < 50:
        suggestions.append(
            "Use more action verbs like: built, developed, "
            "implemented, optimized, delivered"
        )

    if word_count < 300:
        suggestions.append(
            "Your resume seems short. Add more detail to "
            "your experience and projects sections."
        )

    if not suggestions:
        suggestions.append(
            "Great match! Your resume aligns well with this job."
        )

    # ── SCORE LABEL ──
    if final_score >= 75:
        label = "Excellent match"
        color = "green"
    elif final_score >= 55:
        label = "Good match"
        color = "blue"
    elif final_score >= 35:
        label = "Partial match"
        color = "amber"
    else:
        label = "Low match"
        color = "red"

    return {
        "score": final_score,
        "label": label,
        "color": color,
        "breakdown": {
            "tech_skills":   round(tech_score, 1),
            "keyword_match": round(keyword_score, 1),
            "soft_skills":   round(soft_score, 1),
            "action_verbs":  round(action_score, 1),
            "format":        round(format_score, 1),
        },
        "matched": {
            "tech_skills":  list(tech_matched),
            "soft_skills":  list(soft_matched),
            "keywords":     list(keyword_matched)[:20],
        },
        "missing": {
            "tech_skills":  list(missing_tech),
            "soft_skills":  list(missing_soft),
        },
        "suggestions": suggestions,
        "stats": {
            "resume_words":    word_count,
            "job_tech_count":  len(job_tech),
            "tech_matched":    len(tech_matched),
            "action_verbs":    list(resume_actions),
        }
    }


# ── TEST IT DIRECTLY ───────────────────────────────────────────────
# Run: python ats_scorer.py to test

if __name__ == "__main__":
    sample_resume = """
    Software Engineer with 3 years of experience
    building web applications using Python, React, and PostgreSQL.

    EXPERIENCE
    Software Engineer @ TechCorp (2022-Present)
    • Built REST APIs using FastAPI and Python
    • Developed React frontend components
    • Optimized SQL queries improving performance by 40%
    • Deployed applications using Docker and AWS
    • Collaborated with cross-functional teams using Agile

    SKILLS
    Python, JavaScript, React, FastAPI, PostgreSQL,
    Docker, AWS, Git, REST API

    EDUCATION
    Bachelor of Science in Computer Science
    """

    sample_job = """
    We are looking for a Software Engineer with 2+ years of experience.
    Requirements:
    - Python or JavaScript experience required
    - Experience with React or similar frontend framework
    - SQL database knowledge
    - REST API development
    - Docker and cloud experience (AWS preferred)
    - Strong communication and teamwork skills
    - Experience with Agile development
    """

    result = calculate_ats_score(sample_resume, sample_job)

    print(f"\n{'='*50}")
    print(f"ATS SCORE: {result['score']}% — {result['label']}")
    print(f"{'='*50}")
    print(f"\nBreakdown:")
    for k, v in result['breakdown'].items():
        bar = '█' * int(v/10) + '░' * (10 - int(v/10))
        print(f"  {k:20} {bar} {v}%")
    print(f"\nMatched tech skills: {', '.join(result['matched']['tech_skills'])}")
    print(f"Missing tech skills: {', '.join(result['missing']['tech_skills'])}")
    print(f"\nSuggestions:")
    for s in result['suggestions']:
        print(f"  → {s}")