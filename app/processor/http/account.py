import app.exceptions as exc
import app.persistence.database as db
from app.base import do
from app.middleware.headers import get_auth_token
from app.utils import Response, context
from fastapi import APIRouter, Depends, responses

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
