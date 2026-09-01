"""
Authentication service for TeamMemoryOS.

Responsible for validating credentials and issuing JWT access tokens.
Business logic lives here; route handlers stay thin.
"""
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.services.user import get_user_by_email


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the ``User`` if *email* and *password* are valid, else ``None``.

    Verification uses constant-time bcrypt comparison via ``verify_password``.
    """
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login(db: Session, email: str, password: str) -> str | None:
    """Authenticate and return a signed JWT access token, or ``None`` on failure."""
    user = authenticate_user(db, email, password)
    if user is None:
        return None
    return create_access_token(subject=str(user.id))
