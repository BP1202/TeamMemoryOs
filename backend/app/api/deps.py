"""
Shared FastAPI dependencies for TeamMemoryOS.

Provides:
  - get_current_user: resolves the authenticated User from a Bearer JWT.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.dependencies import get_db
from app.models.user import User
from app.services.user import get_user_by_id

import uuid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated ``User`` from the supplied Bearer token.

    Raises HTTP 401 if the token is missing, invalid, expired, or the user
    no longer exists in the database.
    """
    try:
        user_id_str = decode_access_token(token)
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    user = get_user_by_id(db, user_id)
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user
