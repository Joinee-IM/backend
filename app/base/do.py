"""
data objects
"""

from datetime import datetime, time
from typing import Sequence
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.base import enums


class Account(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    gender: enums.GenderType | None
    image_uuid: UUID | None
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
    owner_id: int
    address: str
    contact_number: str | None
    description: str | None
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
    reservation_interval: int | None
    is_reservable: bool
    is_chargeable: bool
    fee_rate: float | None
    fee_type: enums.FeeType | None
    area: int
    current_user_count: int
    capacity: int
    sport_equipments: str | None
    facilities: str | None
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
    remark: str | None
    invitation_code: str
    is_cancelled: bool
    google_event_id: str | None = None


class Court(BaseModel):
    id: int
    venue_id: int
    number: int
    is_published: bool


class ReservationMember(BaseModel):
    reservation_id: int
    account_id: int
    is_manager: bool
    status: enums.ReservationMemberStatus
    source: enums.ReservationMemberSource
