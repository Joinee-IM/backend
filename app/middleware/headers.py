from fastapi import Header

from app import security
from app.utils.context import context


async def get_auth_token(auth_token: str = Header(None, convert_underscores=True)):
    account = None
    if auth_token:
        account = security.decode_jwt(auth_token, context.request_time)
    context.set_account(account)
