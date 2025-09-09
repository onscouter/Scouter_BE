import os
from uuid import UUID
from typing import Any

from dotenv import load_dotenv
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

load_dotenv()

security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ─── Token Creation ────────────────────────────────────────
def create_token(
    sub: str | UUID,
    expires_in_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
    extra: dict[str, Any] = None,
) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    payload: dict[str, Any] = {
        "sub": str(sub),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    if extra:
        payload.update(extra)

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set. Check your .env or environment.")

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_onboarding_token(email: str) -> str:
    return create_token(
        sub=email,
        expires_in_minutes=15,
        extra={"purpose": "onboarding"}
    )


def create_refresh_token(sub: str | UUID) -> str:
    return create_token(
        sub=sub,
        expires_in_minutes=60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        extra={"purpose": "refresh"}
    )


# ─── Token Decoding / Verification ─────────────────────────
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return decode_token(credentials.credentials)


def get_user_id(request: Request) -> str:
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise ValueError
        token = auth_header.removeprefix("Bearer ").strip()
        payload = decode_token(token)
        return payload.get("sub", "anonymous")
    except Exception:
        return "anonymous"


# ─── Response Cookie Helpers ───────────────────────────────
def set_refresh_token(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,  # Set False for local dev if needed
        samesite="strict",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )


def clear_refresh_token(response: Response) -> None:
    response.delete_cookie("refresh_token")
