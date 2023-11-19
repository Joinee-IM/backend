"""
view objects
"""

from datetime import time
from typing import Sequence

from pydantic import BaseModel, NaiveDatetime

from app.base import do


class ViewStadium(do.Stadium):
    city: str
    district: str
    sports: Sequence[str]
    business_hours: Sequence[do.BusinessHour]


class WeekTimeRange(BaseModel):
    weekday: int
    start_time: time
    end_time: time


class DateTimeRange(BaseModel):
    start_time: NaiveDatetime
    end_time: NaiveDatetime
