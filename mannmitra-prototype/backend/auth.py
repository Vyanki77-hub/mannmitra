import os
import re
import time
import secrets
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from db import get_db, User, AuthSession

router = APIRouter(prefix="/auth", tags=["auth"])

# Argon2id password hasher (argon2-cffi defaults to Argon2id)
ph = PasswordHasher()

# Cookie security configuration
COOKIE_NAME = "session_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").strip().lower() in ("true", "1", "yes")

# In-memory rate limiter: key -> list of timestamp floats
# Key format: "{email}:{ip}"
_failed_login_attempts: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 15 * 60  # 15 minutes
MAX_FAILED_ATTEMPTS = 5


def _get_rate_limit_key(email: str, request: Request) -> str:
    client_ip = "unknown"
    if request.client and request.client.host:
        client_ip = request.client.host
    return f"{email}:{client_ip}"


def _check_rate_limit(key: str) -> None:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    # Clean up old attempts
    attempts = [t for t in _failed_login_attempts[key] if t > cutoff]
    _failed_login_attempts[key] = attempts

    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again after 15 minutes.",
        )


def _record_failed_attempt(key: str) -> None:
    _failed_login_attempts[key].append(time.time())


def _clear_rate_limit(key: str) -> None:
    _failed_login_attempts.pop(key, None)


# --------------------------------------------------
# Pydantic Schemas
# --------------------------------------------------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 2 or len(trimmed) > 50:
            raise ValueError("Name must be between 2 and 50 characters.")
        return trimmed

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 128:
            raise ValueError("Password must be between 8 and 128 characters.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _get_current_user_from_cookie(request: Request, db: Session) -> User:
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    token_hash = _hash_token(raw_token)
    session_record = (
        db.query(AuthSession)
        .filter(AuthSession.token_hash == token_hash)
        .first()
    )

    if not session_record or session_record.expires_at < datetime.utcnow():
        # If expired session is found, clean it up
        if session_record:
            db.delete(session_record)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    return session_record.user


# --------------------------------------------------
# Endpoints
# --------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if normalized email is already registered
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Hash password with Argon2id
    password_hash = ph.hash(req.password)

    new_user = User(
        name=req.name,
        email=req.email,
        password_hash=password_hash,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(id=new_user.id, name=new_user.name, email=new_user.email)


@router.post("/login", response_model=UserResponse)
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit_key = _get_rate_limit_key(req.email, request)
    _check_rate_limit(rate_limit_key)

    user = db.query(User).filter(User.email == req.email).first()
    is_valid = False

    if user:
        try:
            is_valid = ph.verify(user.password_hash, req.password)
            if ph.check_needs_rehash(user.password_hash):
                user.password_hash = ph.hash(req.password)
                db.commit()
        except (VerifyMismatchError, InvalidHashError):
            is_valid = False

    if not is_valid or not user:
        _record_failed_attempt(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reset failed attempts on successful login
    _clear_rate_limit(rate_limit_key)

    # Generate cryptographically secure session token
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    # Expiry: 30 days if remember_me, 1 day otherwise
    session_days = 30 if req.remember_me else 1
    duration = timedelta(days=session_days)
    expires_at = datetime.utcnow() + duration

    session_record = AuthSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session_record)
    db.commit()

    # Set secure HttpOnly cookie
    max_age_seconds = int(duration.total_seconds())
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )

    return UserResponse(id=user.id, name=user.name, email=user.email)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(COOKIE_NAME)
    if raw_token:
        token_hash = _hash_token(raw_token)
        session_record = (
            db.query(AuthSession)
            .filter(AuthSession.token_hash == token_hash)
            .first()
        )
        if session_record:
            db.delete(session_record)
            db.commit()

    # Invalidate cookie on client
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user_from_cookie(request, db)
    return UserResponse(id=user.id, name=user.name, email=user.email)
