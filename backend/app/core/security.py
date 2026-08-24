"""
Security utilities for TeamMemoryOS.

Provides:
  - bcrypt password hashing and verification (direct bcrypt, no passlib)
  - JWT access token creation and decoding (via python-jose)
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.settings import settings

# ---------------------------------------------------------------------------
# Password hashing — bcrypt directly
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(subject: str) -> str:
    """Create a signed JWT with *subject* as the ``sub`` claim.

    Expiration is driven by ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """Decode *token* and return the ``sub`` claim.

    Raises ``JWTError`` (from ``jose``) if the token is invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    subject: str | None = payload.get("sub")
    if subject is None:
        raise JWTError("Token payload missing 'sub' claim")
    return subject
