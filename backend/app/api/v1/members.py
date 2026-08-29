from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.organization_member import OrganizationMemberCreate, OrganizationMemberRead
from app.services.organization_member import (
    create_member,
    get_member_by_id,
    get_members_by_organization,
    get_members_by_user,
)

router = APIRouter()


@router.post("/", response_model=OrganizationMemberRead, status_code=status.HTTP_201_CREATED)
def create_new_member(
    member_in: OrganizationMemberCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_member(db, member_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership already exists or referenced organization/user not found",
        )


@router.get("/organization/{organization_id}", response_model=List[OrganizationMemberRead])
def list_members_by_organization(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_members_by_organization(db, organization_id, skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=List[OrganizationMemberRead])
def list_members_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_members_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/{member_id}", response_model=OrganizationMemberRead)
def get_member(
    member_id: UUID,
    db: Session = Depends(get_db),
):
    member = get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )
    return member
