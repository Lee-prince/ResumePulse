# ============================================
# ResumePulse — pdf_generator.py
# Professional US IT resume PDF generator
# No branding, no ATS score on document
# ============================================

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os
import re

# ── COLORS ────────────────────────────────────────────────────────
NAVY      = HexColor("#1B2A4A")
BLACK     = HexColor("#111111")
DARK      = HexColor("#222222")
MID       = HexColor("#444444")
GRAY      = HexColor("#666666")
LGRAY     = HexColor("#999999")
RULE      = HexColor("#2B5BA8")
LIGHTRULE = HexColor("#DDDDDD")


# ── STYLES ────────────────────────────────────────────────────────
def build_styles():
    b = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "ResName", parent=b["Normal"],
            fontSize=22, fontName="Helvetica-Bold",
            textColor=NAVY, spaceAfter=3, leading=26,
        ),
        "contact": ParagraphStyle(
            "ResContact", parent=b["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=MID, spaceAfter=6, leading=12,
        ),
        "section": ParagraphStyle(
            "ResSection", parent=b["Normal"],
            fontSize=10.5, fontName="Helvetica-Bold",
            textColor=NAVY, spaceBefore=10,
            spaceAfter=2, letterSpacing=1.8, leading=13,
        ),
        "job_header": ParagraphStyle(
            "ResJobHeader", parent=b["Normal"],
            fontSize=10.5, fontName="Helvetica-Bold",
            textColor=BLACK, spaceBefore=8,
            spaceAfter=1, leading=13,
        ),
        "bullet": ParagraphStyle(
            "ResBullet", parent=b["Normal"],
            fontSize=9.5, fontName="Helvetica",
            textColor=DARK, leftIndent=14,
            spaceBefore=1.5, spaceAfter=1.5, leading=13.5,
        ),
        "skill_cat": ParagraphStyle(
            "ResSkillCat", parent=b["Normal"],
            fontSize=9.5, fontName="Helvetica-Bold",
            textColor=NAVY, spaceAfter=1, leading=12,
        ),
        "skill_val": ParagraphStyle(
            "ResSkillVal", parent=b["Normal"],
            fontSize=9.5, fontName="Helvetica",
            textColor=DARK, spaceAfter=3,
            leftIndent=10, leading=13,
        ),
        "body": ParagraphStyle(
            "ResBody", parent=b["Normal"],
            fontSize=9.5, fontName="Helvetica",
            textColor=DARK, spaceAfter=2, leading=13,
        ),
        "body_bold": ParagraphStyle(
            "ResBodyBold", parent=b["Normal"],
            fontSize=9.5, fontName="Helvetica-Bold",
            textColor=BLACK, spaceAfter=1, leading=13,
        ),
        "summary": ParagraphStyle(
            "ResSummary", parent=b["Normal"],
            fontSize=9.5, fontName="Helvetica",
            textColor=MID, spaceAfter=4, leading=14.5,
        ),
    }


# ── SECTION HEADER ────────────────────────────────────────────────
def section_rule(S, title):
    return KeepTogether([
        Paragraph(title.upper(), S["section"]),
        HRFlowable(
            width="100%", thickness=1.2,
            color=RULE, spaceAfter=4,
        ),
    ])


# ── PARSER ────────────────────────────────────────────────────────
def parse(text: str) -> dict:
    buckets = {
        "header": [], "summary": [], "experience": [],
        "skills": [], "education": [], "projects": [],
        "certifications": [], "other": []
    }
    markers = {
        "summary":        ["summary", "professional summary",
                          "objective", "profile", "about"],
        "experience":     ["experience", "work experience",
                          "professional experience", "employment",
                          "work history"],
        "skills":         ["skills", "technical skills",
                          "core competencies", "technologies",
                          "technical expertise"],
        "education":      ["education", "academic", "degrees"],
        "projects":       ["projects", "key projects",
                          "personal projects", "notable projects"],
        "certifications": ["certifications", "certificates",
                          "licenses", "achievements", "awards"],
    }

    cur = "header"
    header_done = False

    for raw_line in text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue

        ll  = line.lower().strip(':–—-=# ')
        hit = None

        for sec, keys in markers.items():
            if any(k == ll or ll.startswith(k) for k in keys):
                if len(line) < 50:
                    hit = sec
                    break

        if hit:
            cur = hit
            header_done = True
        else:
            if not header_done:
                buckets["header"].append(line)
            else:
                buckets[cur].append(line)

    return buckets


# ── ROLE DETECTOR ─────────────────────────────────────────────────
def is_role_line(line: str) -> bool:
    has_year   = bool(re.search(r'\b(19|20)\d{2}\b', line))
    has_dash   = any(d in line for d in ("—", "–", " - "))
    has_pres   = "present" in line.lower()
    short      = len(line) < 100
    not_bullet = not line.lstrip().startswith(("•", "-", "*", "▪", "·"))
    return short and not_bullet and (has_year or (has_dash and has_pres))


# ── MAIN PDF BUILDER ──────────────────────────────────────────────
def generate_pdf(
    resume_text: str,
    output_path: str,
    ats_score:   float = None,
    job_title:   str   = "",
    company:     str   = "",
) -> str:

    try:
        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=0.6*inch,
            rightMargin=0.6*inch,
            topMargin=0.55*inch,
            bottomMargin=0.55*inch,
        )

        S    = build_styles()
        flow = []
        secs = parse(resume_text)

        # ── NAME + CONTACT ──────────────────────────────────────
        hdr = secs["header"]
        if hdr:
            flow.append(Paragraph(hdr[0], S["name"]))
            if len(hdr) > 1:
                contact = "   |   ".join(h for h in hdr[1:] if h)
                flow.append(Paragraph(contact, S["contact"]))

        # Thick navy divider under header
        flow.append(HRFlowable(
            width="100%", thickness=2.5,
            color=NAVY, spaceBefore=2, spaceAfter=6,
        ))

        # ── SUMMARY ─────────────────────────────────────────────
        if secs["summary"]:
            flow.append(section_rule(S, "Professional Summary"))
            flow.append(Paragraph(
                " ".join(secs["summary"]), S["summary"]
            ))

        # ── EXPERIENCE ──────────────────────────────────────────
        if secs["experience"]:
            flow.append(section_rule(S, "Professional Experience"))
            for line in secs["experience"]:
                if is_role_line(line):
                    flow.append(Paragraph(line, S["job_header"]))
                    flow.append(HRFlowable(
                        width="100%", thickness=0.4,
                        color=LIGHTRULE, spaceAfter=2,
                    ))
                elif line.lstrip().startswith(("•", "-", "*", "·", "▪")):
                    txt = line.lstrip("•-*·▪ ").strip()
                    flow.append(Paragraph(
                        f"&#9654;&#160;&#160;{txt}",
                        S["bullet"]
                    ))
                elif line:
                    flow.append(Paragraph(line, S["body"]))

        # ── SKILLS ──────────────────────────────────────────────
        if secs["skills"]:
            flow.append(section_rule(S, "Technical Skills"))
            for line in secs["skills"]:
                if ":" in line:
                    cat, val = line.split(":", 1)
                    flow.append(Paragraph(
                        cat.strip(), S["skill_cat"]
                    ))
                    flow.append(Paragraph(
                        val.strip(), S["skill_val"]
                    ))
                elif line:
                    flow.append(Paragraph(line, S["body"]))

        # ── EDUCATION ───────────────────────────────────────────
        if secs["education"]:
            flow.append(section_rule(S, "Education"))
            for line in secs["education"]:
                edu_words = ["b.s.", "m.s.", "b.e.", "b.tech",
                            "bachelor", "master", "mba", "phd",
                            "doctor"]
                if any(e in line.lower() for e in edu_words):
                    flow.append(Paragraph(line, S["body_bold"]))
                elif line:
                    flow.append(Paragraph(line, S["body"]))

        # ── PROJECTS ────────────────────────────────────────────
        if secs["projects"]:
            flow.append(section_rule(S, "Projects"))
            for line in secs["projects"]:
                if line.lstrip().startswith(("•", "-", "*")):
                    flow.append(Paragraph(
                        f"&#9654;&#160;&#160;{line.lstrip('•-* ').strip()}",
                        S["bullet"]
                    ))
                elif "|" in line or (
                    any(d in line for d in ("—", "–")) and
                    len(line) < 80
                ):
                    flow.append(Paragraph(line, S["body_bold"]))
                elif line:
                    flow.append(Paragraph(line, S["body"]))

        # ── CERTIFICATIONS ──────────────────────────────────────
        if secs["certifications"]:
            flow.append(section_rule(S, "Certifications"))
            for line in secs["certifications"]:
                flow.append(Paragraph(
                    f"&#9654;&#160;&#160;{line.lstrip('•-* ').strip()}",
                    S["bullet"]
                ))

        # Build PDF
        doc.build(flow)
        print(f"✅ PDF built successfully: {output_path}")
        return output_path

    except Exception as e:
        import traceback
        print(f"❌ PDF build error: {e}")
        traceback.print_exc()
        return None


# ── TEST ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    from resume_builder import tailor_resume
    import os

    base = """
John Doe
Senior Software Engineer | john@email.com | linkedin.com/in/johndoe | github.com/johndoe | (555) 987-6543 | New York, NY

SUMMARY
Senior software engineer with 5 years of experience building scalable distributed systems.

EXPERIENCE
Senior Software Engineer — FinTech Solutions Inc (2021–Present)
- Architected microservices platform handling 2M daily transactions
- Built data pipelines processing 500GB daily using Apache Kafka and Spark
- Led team of 4 engineers delivering 3 major product releases
- Reduced API response time by 60% through Redis caching implementation
- Implemented CI/CD pipelines reducing deployment time from 2 hours to 15 minutes

Software Engineer — StartupXYZ (2019–2021)
- Developed RESTful APIs using Python Django serving 50,000+ users
- Built React dashboard reducing customer support tickets by 35%
- Migrated monolithic application to microservices on AWS
- Wrote comprehensive test suite achieving 92% code coverage

SKILLS
Python, Java, JavaScript, React, Django, FastAPI, PostgreSQL, MongoDB, Redis, Kafka, Docker, Kubernetes, AWS, Git

EDUCATION
B.S. Computer Science — NYU Tandon School of Engineering (2019)
GPA: 3.8/4.0

PROJECTS
Real-time Analytics Dashboard | React, FastAPI, WebSockets
Reduced reporting lag by 80%

Distributed Task Queue | Python, Redis, Docker
Handles 100K tasks/hour

CERTIFICATIONS
AWS Certified Solutions Architect — Professional
Kubernetes Administrator (CKA)
    """

    jd = """
    Staff Software Engineer — Backend Systems
    5+ years Python/Java, microservices, Kafka, Kubernetes, AWS, PostgreSQL, Redis.
    Distributed systems, CI/CD, team leadership required.
    Design high-scale backend systems, lead technical initiatives, mentor engineers.
    """

    print("Step 1: Calling Groq AI...")
    result = tailor_resume(
        base, jd,
        "John Doe",
        "Staff Software Engineer",
        "TechCorp"
    )

    print(f"Success: {result['success']}")
    if not result['success']:
        print(f"Error: {result.get('error')}")
        exit()

    print(f"ATS Score: {result['ats_score']}%")
    print(f"Original:  {result['original_score']}%")
    print(f"Gain:      +{result['score_improvement']}%")

    print("\nStep 2: Generating PDF...")
    path = generate_pdf(
        resume_text = result["tailored_resume"],
        output_path = "test_final_resume.pdf",
        ats_score   = result["ats_score"],
        job_title   = "Staff Software Engineer",
        company     = "TechCorp"
    )

    if path and os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✅ File size: {size:,} bytes")
        print(f"📄 Open: {os.path.abspath(path)}")
    else:
        print("❌ PDF was not created")