from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # type: ignore


class UserBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)
    is_active: bool = True



class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
