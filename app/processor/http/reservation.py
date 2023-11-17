from typing import Sequence

from fastapi import APIRouter, responses

import app.persistence.database as db
from app.base import do
from app.utils import Response

router = APIRouter(
    tags=['Reservation'],
    default_response_class=responses.JSONResponse,
)
