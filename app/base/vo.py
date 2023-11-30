"""
view objects
"""

from datetime import time
from typing import Sequence

from pydantic import BaseModel, NaiveDatetime

from app.base import do, enums


class ViewStadium(do.Stadium):
    city: str
    district: str
    sports: Sequence[str] | None = None
    business_hours: Sequence[do.BusinessHour]


class WeekTimeRange(BaseModel):
    weekday: int
    start_time: time
    end_time: time


class DateTimeRange(BaseModel):
    start_time: NaiveDatetime
    end_time: NaiveDatetime


class ViewMyReservation(BaseModel):
    reservation_id: int
    start_time: NaiveDatetime
    end_time: NaiveDatetime
    stadium_name: str
    venue_name: str
    is_manager: bool
    vacancy: int
    status: enums.ReservationStatus


class ViewProviderStadium(BaseModel):
    stadium_id: int
    city_name: str
    district_name: str
    stadium_name: str
    venue_count: int
    is_published: bool


class ViewProviderVenue(BaseModel):
    venue_id: int
    stadium_name: str
    venue_name: str
    court_count: int
    area: int
    is_published: bool


class ViewProviderCourt(BaseModel):
    court_id: int
    stadium_name: str
    venue_name: str
    court_number: int
    is_published: bool
