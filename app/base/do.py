"""
data objects
"""

from typing import Optional
from uuid import UUID

from app.base import enums
from pydantic import BaseModel, EmailStr


class Account(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    gender: enums.GenderType
    image_uuid: Optional[UUID]
    role: enums.RoleType
    is_verified: bool
    is_google_login: bool


class GCSFile(BaseModel):
    uuid: UUID
    key: str
    bucket: str
    filename: str
