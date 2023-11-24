from typing import Annotated

from fastapi import Cookie, Header

from app.utils import security
from app.utils.context import context


async def get_auth_token(
    token: Annotated[str | None, Cookie()] = None,
    auth_token: Annotated[str | None, Header(convert_underscores=True)] = None,
):
    account = None
    if token or auth_token:
        account = security.decode_jwt(token or auth_token, context.request_time)
    context.set_account(account)
