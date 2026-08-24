from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.organization_member import MemberRole


class OrganizationMemberBase(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: MemberRole = MemberRole.member
    is_active: bool = True


class OrganizationMemberCreate(OrganizationMemberBase):
    pass


class OrganizationMemberRead(OrganizationMemberBase):
    id: UUID
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
