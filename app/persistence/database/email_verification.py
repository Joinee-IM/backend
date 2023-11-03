from uuid import UUID

from app.persistence.database.util import PostgresQueryExecutor


async def add(account_id: int, email: str) -> UUID:
    code, = await PostgresQueryExecutor(
        sql=fr"INSERT INTO email_verification (account_id, email)"
            fr"     VALUES (%(account_id)s, %(email)s)"
            fr"  RETURNING code",
        account_id=account_id, email=email, fetch=1,
    ).execute()
    return code
