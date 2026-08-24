from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


def create_organization(db: Session, org_in: OrganizationCreate) -> Organization:
    org = Organization(
        name=org_in.name,
        slug=org_in.slug,
        is_active=org_in.is_active,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def get_organization_by_id(db: Session, org_id: UUID) -> Organization | None:
    return db.scalar(select(Organization).where(Organization.id == org_id))


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    return db.scalar(select(Organization).where(Organization.slug == slug))


def get_organizations(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Organization]:
    stmt = select(Organization).offset(skip).limit(limit)
    return db.scalars(stmt).all()
