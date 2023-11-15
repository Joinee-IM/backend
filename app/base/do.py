"""
data objects
"""

from datetime import time
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


class City(BaseModel):
    id: int
    name: str


class Venue(BaseModel):
    id: int
    stadium_id: int
    name: str
    floor: str
    reservation_interval: Optional[int]
    is_reservable: bool
    is_chargeable: bool
    fee_rate: Optional[float]
    fee_type: Optional[enums.FeeType]
    area: int
    current_user_count: int
    capability: int
    sport_equipments: Optional[str]
    facilities: Optional[str]
    court_count: int
    court_type: str
    sport_id: int


class District(BaseModel):
    id: int
    name: str
    city_id: int


class Album(BaseModel):
    id: int
    place_id: int
    type: enums.PlaceType
    file_uuid: UUID


class Sport(BaseModel):
    id: int
    name: str


class BusinessHour(BaseModel):
    id: int
    place_id: int
    type: enums.PlaceType
    weekday: int
    start_time: time
    end_time: time
