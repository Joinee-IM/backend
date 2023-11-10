from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import do, enums
from app.middleware.headers import get_auth_token
from app.utils import Response, context

router = APIRouter(
    tags=['Account'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)]
)


@router.get('/account/{account_id}')
async def read_account(account_id: int) -> Response[do.Account]:
    if account_id != context.account.id:
        raise exc.NoPermission

    account = await db.account.read(account_id=account_id)
    return Response(data=account)


class EditAccountInput(BaseModel):
    nickname: str | None = None
    gender: enums.GenderType | None = None


@router.patch('/account/{account_id}')
async def edit_account(account_id: int, data: EditAccountInput) -> Response[bool]:
    if account_id != context.account.id:
        raise exc.NoPermission

    await db.account.edit(account_id=account_id,
                          nickname=data.nickname,
                          gender=data.gender)
    return Response(data=True)
