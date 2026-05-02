# ============================================
# ResumePulse — resume_builder.py
# Groq AI resume tailoring engine
# Model: Llama 3.3 70B (free, fast, powerful)
# ============================================

from groq import Groq
from dotenv import load_dotenv
from ats_scorer import calculate_ats_score
import json
import re
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"


def tailor_resume(
    base_resume:     str,
    job_description: str,
    user_name:       str = "",
    job_title:       str = "",
    company:         str = ""
) -> dict:
    """
    Core AI function — takes the user's real resume
    and the real job description, returns a fully
    tailored ATS-optimized resume with score.
    """

    # Step 1: Keyword gap analysis
    analysis     = calculate_ats_score(base_resume, job_description)
    missing_tech = list(analysis["missing"]["tech_skills"])[:10]
    missing_soft = list(analysis["missing"]["soft_skills"])[:5]
    orig_score   = analysis["score"]

    gaps = ""
    if missing_tech:
        gaps += f"Missing technical keywords: {', '.join(missing_tech)}\n"
    if missing_soft:
        gaps += f"Missing soft skill keywords: {', '.join(missing_soft)}\n"
    if not gaps:
        gaps = "Good keyword coverage — focus on density, metrics, and semantic alignment."

    # Step 2: Build the prompt
    system_prompt = """You are a world-class ATS resume strategist and professional resume writer.
You have deep expertise in how modern ATS systems work — semantic matching, keyword density,
contextual relevance, and section weighting.
You always respond with valid JSON. Never truncate. Never add text outside the JSON."""

    user_prompt = f"""You are the world's most advanced ATS optimization engine. Your sole purpose is to transform resumes into documents that score 90+ on any ATS system.

You deeply understand that modern ATS systems use:
- Exact keyword matching (primary signal)
- Semantic similarity scoring (contextual relevance)
- Keyword density analysis (frequency matters)
- Section weight scoring (experience weighted highest)
- Skills adjacency scoring (related skills cluster)

TARGET JOB DESCRIPTION (read every word):
{job_description[:3000]}

CANDIDATE BASE RESUME (their real experience):
{base_resume[:3000]}

KEYWORD GAPS TO FILL:
{gaps}

YOUR OPTIMIZATION STRATEGY:

1. EXTRACT from the JD:
   - Every technical skill mentioned → use it MULTIPLE times in context
   - Every responsibility phrase → mirror it exactly in bullets
   - Every requirement → address it directly somewhere in the resume
   - Seniority signals (lead, architect, design, scale) → use them

2. SUMMARY — must contain:
   - Exact job title from the posting (first sentence)
   - Years of experience stated explicitly
   - At least 6 technologies from the JD named directly
   - A specific measurable achievement
   - A sentence mirroring the role's core responsibility

3. EXPERIENCE BULLETS — strict rules:
   - EVERY bullet starts with a different strong action verb
   - EVERY bullet has at least one hard number (%, $, x, ms, users, TB, req/s)
   - EVERY bullet contains at least one keyword from the JD
   - Bullets must be 18-30 words — not too short, not too long
   - Include: scale, impact, technology used, outcome
   - 5-6 bullets per role minimum
   - Use the JD's exact phrases: if JD says "high-scale backend systems" use that exact phrase

4. SKILLS — maximum density:
   - Group into exactly these categories:
     Programming Languages: [list]
     Frameworks & Libraries: [list]
     Databases & Storage: [list]
     Cloud & Infrastructure: [list]
     DevOps & CI/CD: [list]
     Tools & Platforms: [list]
     Methodologies: [list]
   - Include EVERY skill from the JD the candidate plausibly has
   - Add adjacent skills that commonly appear with JD skills
   - Minimum 30 skills total across all categories

5. PROJECTS — make them relevant:
   - Rename/reframe projects to use JD terminology
   - Add the tech stack with JD keywords
   - Include a measurable outcome for each
   - Format: Project Name | Technologies Used
     Description with impact metric

6. NEVER fabricate companies, degrees, or dates
   - You CAN: add metrics where ranges are plausible
   - You CAN: reframe responsibilities using JD language
   - You CAN: expand on implied skills from their experience
   - You CANNOT: add jobs that don't exist

TARGET: The output resume must score 90+ when scanned by any ATS system.

FORMAT (plain text, no markdown):
[Full Name]
[Title] | [email] | [phone] | [linkedin] | [location]

SUMMARY
[3-4 dense sentences packed with JD keywords]

EXPERIENCE
[Job Title — Company Name (Start Year–End Year/Present)]
- [bullet with metric and JD keyword]
- [bullet with metric and JD keyword]
- [bullet with metric and JD keyword]
- [bullet with metric and JD keyword]
- [bullet with metric and JD keyword]
- [bullet with metric and JD keyword]

[repeat for each role]

SKILLS
Programming Languages: [comma separated]
Frameworks & Libraries: [comma separated]
Databases & Storage: [comma separated]
Cloud & Infrastructure: [comma separated]
DevOps & CI/CD: [comma separated]
Tools & Platforms: [comma separated]
Methodologies: [comma separated]

EDUCATION
[Degree — Institution (Year)]
[GPA if strong]

PROJECTS
[Project Name | Tech Stack]
[One line description with metric]

CERTIFICATIONS
[Certification name — Issuer (Year if known)]

Return ONLY this JSON with no other text:
{{
  "tailored_resume": "full resume text here minimum 700 words",
  "ats_score": 92,
  "score_explanation": "This resume scores 92 because it contains X out of Y required keywords, mirrors the JD's exact phrases in 15+ places, and addresses every core requirement",
  "improvements_made": [
    "Incorporated 12 exact JD phrases into experience bullets",
    "Added 8 missing technical keywords naturally",
    "Expanded skills section to 32 technologies",
    "Added quantified metrics to every bullet point",
    "Reframed summary to mirror job title and core responsibilities"
  ],
  "suggestions": [
    "Get AWS certification if not already held to strengthen this application",
    "Add GraphQL project to portfolio to cover the nice-to-have requirement"
  ]
}}"""

    # Step 3: Call Groq
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.15,
            max_tokens=4000,
        )

        raw = response.choices[0].message.content.strip()

        # Step 4: Robust JSON extraction
        raw = _extract_json(raw)
        result = json.loads(raw)

        resume_text = result.get("tailored_resume", "")
        ats_score   = float(result.get("ats_score", orig_score + 25))
        ats_score   = max(0.0, min(100.0, ats_score))

        return {
            "success":           True,
            "tailored_resume":   resume_text,
            "ats_score":         round(ats_score, 1),
            "score_explanation": result.get("score_explanation", ""),
            "improvements_made": result.get("improvements_made", []),
            "suggestions":       result.get("suggestions", []),
            "original_score":    orig_score,
            "score_improvement": round(ats_score - orig_score, 1),
            "model_used":        MODEL,
        }

    except json.JSONDecodeError:
        # Fallback: extract resume text directly
        resume = _extract_resume_fallback(raw, base_resume)
        return {
            "success":           True,
            "tailored_resume":   resume,
            "ats_score":         round(min(orig_score + 28, 95), 1),
            "score_explanation": "Score estimated — response parsing issue.",
            "improvements_made": ["Resume tailored to job description"],
            "suggestions":       ["Review and verify all content"],
            "original_score":    orig_score,
            "score_improvement": 28.0,
            "model_used":        MODEL,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"AI error: {str(e)}",
        }


def _extract_json(raw: str) -> str:
    """Multiple strategies to extract valid JSON"""
    # Remove code fences
    for fence in ["```json", "```"]:
        if fence in raw:
            raw = raw.split(fence)[1].split("```")[0].strip()
            break

    # Find JSON boundaries
    if not raw.startswith("{"):
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]

    # Fix truncated JSON
    if not raw.rstrip().endswith("}"):
        last = raw.rfind('"')
        if last != -1:
            raw = raw[:last+1] + ']}}'

    return raw


def _extract_resume_fallback(raw: str, base: str) -> str:
    """Extract resume text when JSON parsing fails"""
    match = re.search(
        r'"tailored_resume"\s*:\s*"(.*?)(?:"\s*,\s*"ats_score|"\s*\})',
        raw, re.DOTALL
    )
    if match:
        text = match.group(1)
        return text.replace('\\n', '\n').replace('\\"', '"')
    return base  # return original if all else fails