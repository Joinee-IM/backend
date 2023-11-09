"""
data objects
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.base import enums


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


class Stadium(BaseModel):
    id: int
    name: str
    district_id: int
    contact_number: Optional[str]
    description: Optional[str]
    long: float
    lat: float
