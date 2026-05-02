# ============================================
# AI Career Navigator — models.py
# Defines the database tables as Python classes
# SQLAlchemy turns these classes into real tables
# ============================================

from sqlalchemy import (
    Column, Integer, String, Boolean,
    Text, Float, DateTime, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Base is the parent class all our models inherit from
# Think of it as the blueprint factory
Base = declarative_base()


# ── USER TABLE ────────────────────────────────────────────────────
# Stores account information for each user

class User(Base):
    __tablename__ = "users"  # actual table name in SQLite

    # ── Primary Key ──
    id = Column(Integer, primary_key=True, index=True)

    # ── Personal Info ──
    first_name = Column(String(50), nullable=False)
    last_name  = Column(String(50), nullable=False)
    email      = Column(String(100), unique=True, index=True, nullable=False)

    # ── Security ──
    # We NEVER store plain text passwords
    # passlib will hash them before saving
    hashed_password = Column(String(200), nullable=False)

    # ── Profile ──
    years_of_experience = Column(Integer, default=0)

    # ── Settings / Preferences ──
    visa_warning_enabled       = Column(Boolean, default=True)
    experience_warning_enabled = Column(Boolean, default=True)

    # ── Base Resume ──
    # The user's original resume they uploaded during registration
    # This is what Claude will use as the starting point
    base_resume_text = Column(Text, nullable=True)

    # ── Account Status ──
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationship ──
    # One user can have MANY tailored resumes
    # This lets us do user.resumes to get all their resumes
    resumes = relationship("TailoredResume", back_populates="owner")

    def __repr__(self):
        return f"<User {self.email}>"


# ── TAILORED RESUME TABLE ─────────────────────────────────────────
# Every time Claude generates a resume, we save it here
# So the user can go back and download previous resumes

class TailoredResume(Base):
    __tablename__ = "tailored_resumes"

    # ── Primary Key ──
    id = Column(Integer, primary_key=True, index=True)

    # ── Foreign Key ──
    # Links this resume back to the user who owns it
    # If user is deleted, their resumes are deleted too (cascade)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # ── Job Info ──
    job_title   = Column(String(200), nullable=True)
    company     = Column(String(200), nullable=True)
    job_url     = Column(String(500), nullable=True)

    # ── The actual text ──
    job_description_text  = Column(Text, nullable=False)  # what we scraped
    tailored_resume_text  = Column(Text, nullable=False)  # what Claude made
    pdf_path              = Column(String(500), nullable=True)  # where PDF is saved

    # ── ATS Score ──
    # How well the resume matches the job (0-100)
    ats_score = Column(Float, nullable=True)

    # ── Visa/Experience flags ──
    # Did this job have warnings? Good to track
    had_visa_warning       = Column(Boolean, default=False)
    had_experience_warning = Column(Boolean, default=False)

    # ── Timestamps ──
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── Relationship back to user ──
    owner = relationship("User", back_populates="resumes")

    def __repr__(self):
        return f"<TailoredResume job={self.job_title} score={self.ats_score}>"


# ── WHAT THESE RELATIONSHIPS MEAN ─────────────────────────────────
#
#  User (1) ──────────────── TailoredResume (many)
#
#  One user can have many tailored resumes
#  Each tailored resume belongs to exactly one user
#
#  In code this means:
#    user.resumes          → list of all their resumes
#    resume.owner          → the user who owns it
#    resume.owner.email    → the user's email