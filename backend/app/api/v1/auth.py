"""
Authentication endpoints for TeamMemoryOS.

POST /auth/login  — issue a JWT access token via OAuth2 password flow.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.auth import Token
from app.services.auth import login

router = APIRouter()


@router.post("/login", response_model=Token)
def auth_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Exchange valid email/password credentials for a JWT access token.

    Uses the standard OAuth2 password flow — ``username`` maps to the user's
    email address.
    """
    token = login(db, email=form_data.username, password=form_data.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=token)
