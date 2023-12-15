from typing import Sequence
from uuid import UUID

import asyncpg

import app.exceptions as exc
from app.base import do, enums
from app.base.enums import GenderType, RoleType
from app.persistence.database import pg_pool_handler
from app.persistence.database.util import PostgresQueryExecutor


async def add(
    email: str,
    pass_hash: str | None = None,
    nickname: str | None = None,
    gender: GenderType = None,
    role: RoleType = RoleType.normal,
    is_google_login: bool = False,
    access_token: str | None = None,
    refresh_token: str | None = None,
    is_verified: bool = False,
) -> int:
    id_, = await PostgresQueryExecutor(
        sql=r'INSERT INTO account'
            r'            (email, pass_hash, nickname, gender, role, is_google_login, '
            r'             access_token, refresh_token, is_verified)'
            r'     VALUES (%(email)s, %(pass_hash)s, %(nickname)s, %(gender)s, %(role)s, %(is_google_login)s,'
            r'             %(access_token)s, %(refresh_token)s, %(is_verified)s)'
            r'  RETURNING id',
        email=email, pass_hash=pass_hash, nickname=nickname, gender=gender, role=role,
        is_google_login=is_google_login, access_token=access_token, refresh_token=refresh_token,
        is_verified=is_verified,
    ).fetch_one()
    return id_


async def read_by_email(email: str, include_unverified: bool = False) -> tuple[int, str, RoleType, bool]:
    """
    :return: (account_id, pass_hash, role)
    """
    try:
        id_, pass_hash, role, is_verified = await PostgresQueryExecutor(
            sql=fr'SELECT id, pass_hash, role, is_verified'
                fr'  FROM account'
                fr' WHERE email = %(email)s'
                fr'{" AND is_verified" if not include_unverified else ""}',
            email=email,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return id_, pass_hash, role, is_verified


async def read(account_id: int) -> do.Account:
    try:
        id_, email, nickname, gender, image_uuid, role, is_verified, is_google_login = await PostgresQueryExecutor(
            sql=r'SELECT id, email, nickname, gender, image_uuid, role, is_verified, is_google_login'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return do.Account(
        id=id_, email=email, nickname=nickname, gender=gender, image_uuid=image_uuid,
        role=role, is_verified=is_verified, is_google_login=is_google_login,
    )


async def reset_password(code: str, pass_hash: str) -> None:
    async with pg_pool_handler.cursor() as cursor:
        cursor: asyncpg.connection.Connection
        try:
            account_id, = await cursor.fetchrow(
                'UPDATE email_verification'
                '   SET is_consumed = $1'
                ' WHERE code = $2'
                '   AND is_consumed = $3'
                ' RETURNING account_id',
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
            r"       is_google_login = %(is_google_login)s,"
            r"       is_verified = %(is_verified)s"
            r" WHERE id = %(account_id)s",
        access_token=access_token, refresh_token=refresh_token, is_google_login=True, account_id=account_id,
        is_verified=True,
    ).execute()


async def edit(
    account_id: int,
    pass_hash: str | None = None,
    nickname: str | None = None,
    gender: GenderType | None = None,
    image_uuid: UUID | None = None,
    role: enums.RoleType | None = None,
) -> None:
    to_update = {}
    if pass_hash:
        to_update['pass_hash'] = pass_hash
    if nickname:
        to_update['nickname'] = nickname
    if gender:
        to_update['gender'] = gender
    if image_uuid:
        to_update['image_uuid'] = image_uuid
    if role:
        to_update['role'] = role

    if not to_update:
        return

    update_sql = ', '.join([f'{field} = %({field})s' for field in to_update])
    await PostgresQueryExecutor(
        sql=fr'UPDATE account'
            fr'   SET {update_sql}'
            fr' WHERE id = %(account_id)s',
        account_id=account_id, **to_update,
    ).execute()


async def search(query: str) -> Sequence[do.Account]:
    results = await PostgresQueryExecutor(
        sql=r'SELECT id, email, nickname, gender, image_uuid, role, is_verified, is_google_login'
            r'  FROM account'
            r' WHERE (email LIKE %(query)s'
            r'    OR nickname LIKE %(query)s)'
            r'   AND is_verified = %(is_verified)s',
        query=f'%{query}%', is_verified=True,
    ).fetch_all()

    return [
        do.Account(
            id=id_, email=email, nickname=nickname, gender=gender, image_uuid=image_uuid,
            role=role, is_verified=is_verified, is_google_login=is_google_login,
        )
        for id_, email, nickname, gender, image_uuid, role, is_verified, is_google_login in results
    ]


async def get_google_token(account_id: int) -> tuple[str, str]:
    access_token, refresh_token = await PostgresQueryExecutor(
        sql=r"SELECT access_token, refresh_token"
            r"  FROM account"
            r" WHERE id = %(account_id)s",
        account_id=account_id,
    ).fetch_one()

    return access_token, refresh_token


async def batch_read(account_ids: Sequence[int], include_unverified: bool = False) -> Sequence[do.Account]:
    if not account_ids:
        return []

    params = {fr'account_{i}': uuid for i, uuid in enumerate(account_ids)}
    in_sql = ', '.join([fr'%({param})s' for param in params])

    results = await PostgresQueryExecutor(
        sql=fr'SELECT id, email, nickname, gender, image_uuid, role, is_verified, is_google_login'
            fr'  FROM account'
            fr' WHERE id IN ({in_sql})'
            fr'{" AND is_verified" if not include_unverified else ""}',
        **params,
    ).fetch_all()
    return [
        do.Account(
            id=id_, email=email, nickname=nickname, gender=gender, image_uuid=image_uuid,
            role=role, is_verified=is_verified, is_google_login=is_google_login,
        )
        for id_, email, nickname, gender, image_uuid, role, is_verified, is_google_login in results
    ]
