# ============================================
# AI Career Navigator — auth.py
# Handles password hashing and JWT tokens
# NEVER stores plain text passwords
# ============================================

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# ── PASSWORD HASHING ──────────────────────────────────────────────
# bcrypt turns "mypassword123" into something like:
# "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
# This is a one-way process — you can never reverse it
# We only ever COMPARE hashes, never decrypt them

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(plain_password: str) -> str:
    """Turn a plain password into a secure hash"""
    # bcrypt has a 72 byte limit — truncate safely
    return pwd_context.hash(plain_password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plain password matches a stored hash"""
    return pwd_context.verify(plain_password[:72], hashed_password)


# ── JWT TOKENS ────────────────────────────────────────────────────
# JWT = JSON Web Token
# Think of it like a stamped ticket at an event:
#   - The stamp proves it's real (our SECRET_KEY signs it)
#   - It has an expiry time
#   - The user sends it with every request to prove they're logged in

SECRET_KEY    = os.getenv("SECRET_KEY", "fallback-secret-change-this")
ALGORITHM     = "HS256"           # signing algorithm
TOKEN_EXPIRES = 60 * 24 * 7      # token lasts 7 days (in minutes)

def create_access_token(user_id: int, email: str) -> str:
    """
    Creates a JWT token for a logged-in user
    This token gets sent to the browser and stored
    The extension sends it with every API request
    """
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRES)

    # The "payload" is the data we encode into the token
    payload = {
        "sub": str(user_id),   # subject = user's id
        "email": email,
        "exp": expire          # expiry time
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT token
    Returns the payload if valid, raises error if not
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── GET CURRENT USER ──────────────────────────────────────────────
# This is used by FastAPI endpoints that require login
# It reads the token from the request header
# and returns the current user from the database

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User

# This tells FastAPI where to look for the token
# Clients send: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency — protects routes that need login
    Usage: add  current_user: User = Depends(get_current_user)
    to any endpoint that requires authentication
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"}
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_error

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_error

    # Look up the user in the database
    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    return user