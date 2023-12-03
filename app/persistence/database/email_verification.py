from uuid import UUID

import app.exceptions as exc
from app.persistence.database.util import PostgresQueryExecutor


async def add(account_id: int, email: str) -> UUID:
    code, = await PostgresQueryExecutor(
        sql=r"INSERT INTO email_verification (account_id, email)"
            r"     VALUES (%(account_id)s, %(email)s)"
            r"  RETURNING code",
        account_id=account_id, email=email,
    ).fetch_one()
    return code


async def verify_email(code: UUID):
    try:
        account_id, = await PostgresQueryExecutor(
            sql=r'UPDATE email_verification'
                r'   SET is_consumed = %(is_consumed)s'
                r' WHERE code = %(code)s'
                r' RETURNING account_id',
            is_consumed=True, code=code,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    await PostgresQueryExecutor(
        sql=r'UPDATE account'
            r'   SET is_verified = %(is_verified)s'
            r' WHERE id = %(account_id)s',
        is_verified=True, account_id=account_id,
    ).execute()


async def read(account_id: int, email: str) -> UUID:
    try:
        code, = await PostgresQueryExecutor(
            sql=r'SELECT code'
                r'  FROM email_verification'
                r' WHERE account_id = %(account_id)s AND email = %(email)s',
            email=email, account_id=account_id,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return code
