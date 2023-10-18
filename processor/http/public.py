from typing import Optional

from fastapi import APIRouter, responses
from pydantic import BaseModel

router = APIRouter(tags=['Public'])


@router.get("/", status_code=200, response_class=responses.HTMLResponse)
async def default_page():
    return "<a href=\"/docs\">/docs</a>"


class HealthCheckOutput(BaseModel):
    health: Optional[str] = 'ok'


@router.get("/health")
async def health_check() -> HealthCheckOutput:
    return HealthCheckOutput(health='ok')
