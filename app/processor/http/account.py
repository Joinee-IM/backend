from dataclasses import dataclass

from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
import app.persistence.email as email
from app.base.enums import GenderType, RoleType
from app.middleware.headers import get_auth_token
from app.security import hash_password
from app.utils.response import Response

router = APIRouter(
    tags=['Account'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)]
)


class AddAccountInput(BaseModel):
    email: str
    password: str
    nickname: str
    gender: GenderType
    role: RoleType


@dataclass
class AddAccountOutput:
    id: int


@router.post('/account')
async def add_account(data: AddAccountInput) -> Response[AddAccountOutput]:
    try:
        account_id = await db.account.add(
            email=data.email,
            pass_hash=hash_password(data.password),
            nickname=data.nickname,
            gender=data.gender,
            role=data.role,
            is_google_login=False,
        )
    except exc.UniqueViolationError:
        raise exc.EmailExists
    code = await db.email_verification.add(account_id=account_id, email=data.email)
    await email.verification.send(to=data.email, code=str(code))
    return Response(data=AddAccountOutput(id=account_id))
