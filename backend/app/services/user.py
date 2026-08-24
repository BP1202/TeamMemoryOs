import hashlib
import secrets
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def _hash_password(password: str) -> str:
    """Deterministic password hash using SHA-256 + random salt.

    NOTE: This is a temporary stub for the pre-auth sprint.
    Replace with bcrypt/argon2 when authentication is implemented.
    """
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=_hash_password(user_in.password),
        is_active=user_in.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.id == user_id))


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[User]:
    return db.scalars(select(User).offset(skip).limit(limit)).all()
