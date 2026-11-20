from datetime import UTC, datetime, timedelta
import hashlib
import secrets

import jwt

from app.core.config import (
    ACCESS_TOKEN_MINUTES,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_DAYS,
    SIMULATED_OTP,
)


def hash_otp(phone_number: str, otp_code: str = SIMULATED_OTP) -> str:
    return hashlib.sha256(f"{phone_number}:{otp_code}".encode()).hexdigest()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        },
        JWT_SECRET_KEY,
        algorithm="HS256",
    )


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS)


def is_expired(expiry: datetime, now: datetime | None = None) -> bool:
    current_time = now or datetime.now(UTC)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    return expiry <= current_time
