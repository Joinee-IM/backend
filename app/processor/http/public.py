from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.utils.response import Response
from app.security import verify_password, encode_jwt
import app.exceptions as exc


router = APIRouter(tags=['Public'])


@router.get("/", status_code=200, response_class=responses.HTMLResponse)
async def default_page():
    return "<a href=\"/docs\">/docs</a>"


class HealthCheckOutput(BaseModel):
    health: Optional[str] = 'ok'


@router.get("/health")
async def health_check() -> Response[HealthCheckOutput]:
    return Response(data=HealthCheckOutput(health='ok'))


class LoginInput(BaseModel):
    username: str
    password: str


@dataclass
class LoginOutput:
    account_id: int
    token: str


@router.post('/login')
async def login(data: LoginInput) -> Response[LoginOutput]:
    try:
        account_id, pass_hash, role = await db.account.read_by_username(data.username)
    except TypeError:
        raise exc.LoginFailed

    if not verify_password(data.password, pass_hash):
        raise exc.LoginFailed

    token = encode_jwt(account_id=account_id, role=role)
    return Response(data=LoginOutput(account_id=account_id, token=token))
