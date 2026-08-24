from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services.organization import (
    create_organization,
    get_organization_by_id,
    get_organization_by_slug,
    get_organizations,
)

router = APIRouter()


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_new_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
):
    existing = get_organization_by_slug(db, org_in.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with slug '{org_in.slug}' already exists",
        )
    return create_organization(db, org_in)


@router.get("/", response_model=List[OrganizationRead])
def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_organizations(db, skip=skip, limit=limit)


@router.get("/{org_id}", response_model=OrganizationRead)
def get_organization(
    org_id: UUID,
    db: Session = Depends(get_db),
):
    org = get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return org
