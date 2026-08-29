from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization_member import OrganizationMember
from app.schemas.organization_member import OrganizationMemberCreate


def create_member(
    db: Session, member_in: OrganizationMemberCreate
) -> OrganizationMember:
    member = OrganizationMember(
        organization_id=member_in.organization_id,
        user_id=member_in.user_id,
        role=member_in.role,
        is_active=member_in.is_active,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_member_by_id(db: Session, member_id: UUID) -> OrganizationMember | None:
    return db.scalar(
        select(OrganizationMember).where(OrganizationMember.id == member_id)
    )


def get_members_by_organization(
    db: Session, organization_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[OrganizationMember]:
    stmt = (
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == organization_id)
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


def get_members_by_user(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[OrganizationMember]:
    stmt = (
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()
