"""
data objects
"""

from datetime import datetime, time
from typing import Optional, Sequence
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
    is_published: bool


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
    is_published: bool


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


class Reservation(BaseModel):
    id: int
    stadium_id: int
    venue_id: int
    court_id: int
    start_time: datetime
    end_time: datetime
    member_count: int
    vacancy: int
    technical_level: Sequence[enums.TechnicalType]
    remark: Optional[str]
    invitation_code: str
    is_cancelled: bool
    google_event_id: Optional[str] = None


class Court(BaseModel):
    id: int
    venue_id: int
    is_published: bool


class ReservationMember(BaseModel):
    reservation_id: int
    account_id: int
    is_joined: bool
    is_manager: bool
