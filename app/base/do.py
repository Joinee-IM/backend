"""
data objects
"""

from dataclasses import dataclass
from uuid import UUID

from app.base import enums


@dataclass
class Account:
    id: int
    username: str
    role: enums.RoleType
    real_name: str
    student_id: str


@dataclass
class GCSFile:
    uuid: UUID
    key: str
    bucket: str
    filename: str
