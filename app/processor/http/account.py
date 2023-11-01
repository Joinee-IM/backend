from dataclasses import dataclass

from fastapi import APIRouter, responses, Depends
from pydantic import BaseModel

from app.security import hash_password
from app.middleware.headers import get_auth_token
from app.utils.response import Response
import app.persistence.database as db


router = APIRouter(
    tags=['Account'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)]
)


class AddAccountInput(BaseModel):
    username: str
    password: str
    real_name: str
    student_id: str


@dataclass
class AddAccountOutput:
    id: int


@router.post('/account')
async def add_account(data: AddAccountInput) -> Response[AddAccountOutput]:

    account_id = await db.account.add(username=data.username,
                                      pass_hash=hash_password(data.password))

    return Response(data=AddAccountOutput(id=account_id))
