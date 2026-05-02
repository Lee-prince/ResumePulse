# ============================================
# ResumePulse — main.py
# FastAPI backend — complete final version
# ============================================

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import re
import time

from database import get_db, create_tables
from models import User, TailoredResume
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)
from dotenv import load_dotenv

load_dotenv()


# ── APP ───────────────────────────────────────────────────────────
app = FastAPI(
    title="ResumePulse API",
    version="1.0.0",
    description="Backend for ResumePulse Chrome Extension"
)


# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "chrome-extension://*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── STARTUP ───────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    create_tables()
    print("🚀 ResumePulse API is running!")


# ── SCHEMAS ───────────────────────────────────────────────────────

class UserRegister(BaseModel):
    first_name:          str
    last_name:           str
    email:               str
    password:            str
    years_of_experience: Optional[int] = 0
    base_resume_text:    Optional[str] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email:    str
    password: str

class UpdateSettings(BaseModel):
    visa_warning_enabled:       Optional[bool] = None
    experience_warning_enabled: Optional[bool] = None
    years_of_experience:        Optional[int]  = None

class UpdateResume(BaseModel):
    base_resume_text: str

class TailorRequest(BaseModel):
    job_description: str
    job_title:       Optional[str] = None
    company:         Optional[str] = None
    job_url:         Optional[str] = None


# ══════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════

# ── HEALTH ────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "running", "message": "ResumePulse API is healthy!", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "ResumePulse API", "docs": "http://localhost:8000/docs"}


# ── REGISTER ──────────────────────────────────────────────────────
@app.post("/auth/register", status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(
            User.email == user_data.email.lower()
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")

        hashed = hash_password(user_data.password)

        new_user = User(
            first_name          = user_data.first_name.strip(),
            last_name           = user_data.last_name.strip(),
            email               = user_data.email.lower().strip(),
            hashed_password     = hashed,
            years_of_experience = user_data.years_of_experience or 0,
            base_resume_text    = user_data.base_resume_text,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(new_user.id, new_user.email)

        return {
            "message": "Account created successfully!",
            "token":   token,
            "user": {
                "id":                         new_user.id,
                "first_name":                 new_user.first_name,
                "last_name":                  new_user.last_name,
                "email":                      new_user.email,
                "years_of_experience":        new_user.years_of_experience,
                "visa_warning_enabled":       new_user.visa_warning_enabled,
                "experience_warning_enabled": new_user.experience_warning_enabled,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"REGISTER ERROR: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ── LOGIN ─────────────────────────────────────────────────────────
@app.post("/auth/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == credentials.email.lower()
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated.")

    token = create_access_token(user.id, user.email)

    return {
        "message": "Logged in successfully!",
        "token":   token,
        "user": {
            "id":                         user.id,
            "first_name":                 user.first_name,
            "last_name":                  user.last_name,
            "email":                      user.email,
            "years_of_experience":        user.years_of_experience,
            "visa_warning_enabled":       user.visa_warning_enabled,
            "experience_warning_enabled": user.experience_warning_enabled,
        }
    }


# ── GET MY PROFILE ────────────────────────────────────────────────
@app.get("/user/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id":                         current_user.id,
        "first_name":                 current_user.first_name,
        "last_name":                  current_user.last_name,
        "email":                      current_user.email,
        "years_of_experience":        current_user.years_of_experience,
        "visa_warning_enabled":       current_user.visa_warning_enabled,
        "experience_warning_enabled": current_user.experience_warning_enabled,
        "has_resume":                 bool(current_user.base_resume_text),
        "resume_count":               len(current_user.resumes),
        "created_at":                 current_user.created_at,
    }


# ── UPDATE SETTINGS ───────────────────────────────────────────────
@app.put("/user/settings")
def update_settings(
    settings:     UpdateSettings,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    if settings.visa_warning_enabled is not None:
        current_user.visa_warning_enabled = settings.visa_warning_enabled
    if settings.experience_warning_enabled is not None:
        current_user.experience_warning_enabled = settings.experience_warning_enabled
    if settings.years_of_experience is not None:
        current_user.years_of_experience = settings.years_of_experience

    db.commit()
    db.refresh(current_user)

    return {
        "message":                    "Settings updated!",
        "visa_warning_enabled":       current_user.visa_warning_enabled,
        "experience_warning_enabled": current_user.experience_warning_enabled,
        "years_of_experience":        current_user.years_of_experience,
    }


# ── UPDATE BASE RESUME ────────────────────────────────────────────
@app.put("/user/resume")
def update_base_resume(
    resume_data:  UpdateResume,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    current_user.base_resume_text = resume_data.base_resume_text
    db.commit()
    return {"message": "Base resume saved successfully!", "length": len(resume_data.base_resume_text)}


# ── GET MY RESUMES ────────────────────────────────────────────────
@app.get("/user/resumes")
def get_my_resumes(
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    resumes = db.query(TailoredResume).filter(
        TailoredResume.user_id == current_user.id
    ).order_by(TailoredResume.created_at.desc()).all()

    return {
        "count": len(resumes),
        "resumes": [
            {
                "id":                  r.id,
                "job_title":           r.job_title,
                "company":             r.company,
                "ats_score":           r.ats_score,
                "tailored_resume_text": r.tailored_resume_text,
                "created_at":          r.created_at,
                "had_visa_warning":    r.had_visa_warning,
                "had_experience_warning": r.had_experience_warning,
            }
            for r in resumes
        ]
    }


# ── TAILOR RESUME ─────────────────────────────────────────────────
@app.post("/resume/tailor")
def tailor_resume_endpoint(
    request:      TailorRequest,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    # 1. Check user has a base resume
    if not current_user.base_resume_text:
        raise HTTPException(
            status_code=400,
            detail="Please upload your base resume in settings first."
        )

    # 2. Import AI modules
    from resume_builder import tailor_resume
    from pdf_generator  import generate_pdf

    print(f"Tailoring resume for: {current_user.email}")
    print(f"Job: {request.job_title} at {request.company}")

    # 3. Call Groq AI
    result = tailor_resume(
        base_resume     = current_user.base_resume_text,
        job_description = request.job_description,
        user_name       = f"{current_user.first_name} {current_user.last_name}",
        job_title       = request.job_title or "",
        company         = request.company   or "",
    )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {result.get('error', 'Unknown error')}"
        )

    # 4. Generate PDF
    pdf_dir      = "generated_resumes"
    pdf_filename = f"resume_{current_user.id}_{int(time.time())}.pdf"
    pdf_path     = os.path.join(pdf_dir, pdf_filename)
    os.makedirs(pdf_dir, exist_ok=True)

    generate_pdf(
        resume_text = result["tailored_resume"],
        output_path = pdf_path,
        ats_score   = result["ats_score"],
        job_title   = request.job_title or "This Role",
        company     = request.company   or "",
    )

    # 5. Save to database
    new_resume = TailoredResume(
        user_id              = current_user.id,
        job_title            = request.job_title,
        company              = request.company,
        job_url              = request.job_url,
        job_description_text = request.job_description,
        tailored_resume_text = result["tailored_resume"],
        pdf_path             = pdf_path,
        ats_score            = result["ats_score"],
        had_visa_warning     = False,
        had_experience_warning = False,
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    # 6. Return response to extension
    return {
        "message":           "Resume tailored successfully!",
        "resume_id":         new_resume.id,
        "tailored_resume":   result["tailored_resume"],
        "ats_score":         result["ats_score"],
        "original_score":    result["original_score"],
        "score_improvement": result["score_improvement"],
        "score_explanation": result["score_explanation"],
        "improvements_made": result["improvements_made"],
        "suggestions":       result["suggestions"],
        "pdf_url":           f"http://localhost:8000/download/{new_resume.id}",
    }


# ── DELETE RESUME ─────────────────────────────────────────────────
@app.delete("/resume/{resume_id}")
def delete_resume(
    resume_id:    int,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    resume = db.query(TailoredResume).filter(
        TailoredResume.id      == resume_id,
        TailoredResume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully."}


# ── PDF DOWNLOAD ──────────────────────────────────────────────────
@app.get("/download/{resume_id}")
def download_pdf(
    resume_id: int,
    token:     str     = None,
    db:        Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    from auth import decode_access_token

    # Require token as query parameter
    if not token:
        raise HTTPException(status_code=401, detail="Token required")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = int(payload.get("sub", 0))

    resume = db.query(TailoredResume).filter(
        TailoredResume.id      == resume_id,
        TailoredResume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if not resume.pdf_path or not os.path.exists(resume.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on server.")

    # Build filename: JobTitle_YYYYMMDD_HHMM.pdf
    job_part  = re.sub(r'[^\w\s-]', '', resume.job_title or "Resume").strip()
    job_part  = re.sub(r'\s+', '_', job_part)
    date_part = resume.created_at.strftime("%Y%m%d_%H%M") if resume.created_at else datetime.now().strftime("%Y%m%d_%H%M")
    filename  = f"{job_part}_{date_part}.pdf"

    return FileResponse(
        path       = resume.pdf_path,
        filename   = filename,
        media_type = "application/pdf",
        headers    = {
            "Content-Disposition":        f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
        }
    )