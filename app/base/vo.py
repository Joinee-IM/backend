"""
view objects
"""

from typing import Sequence

from app.base import do, enums


class ViewStadium(do.Stadium):
    city: str
    district: str
    sports: Sequence[str]
    business_hours: Sequence[do.BusinessHour]