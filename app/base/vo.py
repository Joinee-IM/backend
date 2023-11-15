"""
view objects
"""

from datetime import time
from typing import Sequence

from pydantic import BaseModel

from app.base import do, enums


class ViewStadium(do.Stadium):
    city: str
    district: str
    sports: Sequence[str]
    business_hours: Sequence[do.BusinessHour]


class TimeRange(BaseModel):
    weekday: int
    start_time: time
    end_time: time
