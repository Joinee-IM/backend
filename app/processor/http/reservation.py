from typing import Sequence

from fastapi import APIRouter, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import do, vo
from app.utils import Limit, Offset, Response

router = APIRouter(
    tags=['Reservation'],
    default_response_class=responses.JSONResponse,
)
