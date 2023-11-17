from typing import Optional
from uuid import UUID

import asyncpg

import app.exceptions as exc
from app.base import do
from app.base.enums import GenderType, RoleType
from app.persistence.database import pg_pool_handler
from app.persistence.database.util import PostgresQueryExecutor


async def add(
    email: str,
    pass_hash: Optional[str] = None,
    nickname: Optional[str] = None,
    gender: GenderType = GenderType.unrevealed,
    role: RoleType = RoleType.normal,
    is_google_login: bool = False,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> int:
    id_, = await PostgresQueryExecutor(
        sql=r'INSERT INTO account'
            r'            (email, pass_hash, nickname, gender, role, is_google_login, access_token, refresh_token)'
            r'     VALUES (%(email)s, %(pass_hash)s, %(nickname)s, %(gender)s, %(role)s, %(is_google_login)s,'
            r'             %(access_token)s, %(refresh_token)s)'
            r'  RETURNING id',
        email=email, pass_hash=pass_hash, nickname=nickname, gender=gender, role=role,
        is_google_login=is_google_login, access_token=access_token, refresh_token=refresh_token,
        fetch=1,
    ).execute()
    return id_


async def read_by_email(email: str) -> tuple[int, str, RoleType, bool]:
    """
    :return: (account_id, pass_hash, role)
    """
    try:
        id_, pass_hash, role, is_verified = await PostgresQueryExecutor(
            sql=r'SELECT id, pass_hash, role, is_verified'
                r'  FROM account'
                r' WHERE email = %(email)s',
            email=email, fetch=1,
        ).execute()
    except TypeError:
        raise exc.NotFound

    return id_, pass_hash, RoleType(role), is_verified


async def read(account_id: int) -> do.Account:
    try:
        id_, email, nickname, gender, image_uuid, role, is_verified, is_google_login = await PostgresQueryExecutor(
            sql=r'SELECT id, email, nickname, gender, image_uuid, role, is_verified, is_google_login'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id, fetch=1,
        ).execute()
    except TypeError:
        raise exc.NotFound

    return do.Account(
        id=id_, email=email, nickname=nickname, gender=GenderType(gender), image_uuid=image_uuid,
        role=RoleType(role), is_verified=is_verified, is_google_login=is_google_login,
    )


async def reset_password(code: str, pass_hash: str) -> None:
    async with pg_pool_handler.cursor() as cursor:
        cursor: asyncpg.connection.Connection
        try:
            account_id, = await cursor.fetchrow(
                'UPDATE email_verification'
                '   SET is_consumed = $1'
                ' WHERE code = $2'
                '   AND is_consumed = $3',
                True, code, False,
            )
        except TypeError:
            raise exc.NotFound
        await cursor.execute(
            r'UPDATE account'
            r'   SET pass_hash = $1'
            r' WHERE id = $2',
            pass_hash, account_id,
        )


async def update_google_token(account_id: int, access_token: str, refresh_token: str) -> None:
    await PostgresQueryExecutor(
        sql=r"UPDATE account"
            r"   SET access_token = %(access_token)s,"
            r"       refresh_token = %(refresh_token)s,"
            r"       is_google_login = %(is_google_login)s"
            r" WHERE id = %(account_id)s",
        access_token=access_token, refresh_token=refresh_token, is_google_login=True, account_id=account_id,
        fetch=None,
    ).execute()


async def edit(
    account_id: int,
    nickname: Optional[str] = None,
    gender: Optional[GenderType] = None,
    image_uuid: Optional[UUID] = None,
) -> None:
    to_update = {}
    if nickname:
        to_update['nickname'] = nickname
    if gender:
        to_update['gender'] = gender
    if image_uuid:
        to_update['image_uuid'] = image_uuid

    if not to_update:
        return

    update_sql = ', '.join([f'{field} = %({field})s' for field in to_update])
    await PostgresQueryExecutor(
        sql=fr'UPDATE account'
            fr'   SET {update_sql}'
            fr' WHERE id = %(account_id)s',
        account_id=account_id, **to_update, fetch=None,
    ).execute()
