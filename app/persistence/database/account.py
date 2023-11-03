import app.exceptions as exc
from app.base import do
from app.base.enums import GenderType, RoleType
from app.persistence.database.util import PostgresQueryExecutor


async def add(email: str, pass_hash: str, nickname: str,
              gender: GenderType = GenderType.unrevealed,
              role: RoleType = RoleType.normal,
              is_google_login: bool = False) -> int:
    id_, = await PostgresQueryExecutor(
        sql=r'INSERT INTO account'
            r'            (email, pass_hash, nickname, gender, role, is_google_login)'
            r'     VALUES (%(email)s, %(pass_hash)s, %(nickname)s, %(gender)s, %(role)s, %(is_google_login)s)'
            r'  RETURNING id',
        email=email, pass_hash=pass_hash, nickname=nickname, gender=gender, role=role, is_google_login=is_google_login,
        fetch=1,
    ).execute()
    return id_


async def read_by_email(email: str) -> tuple[int, str, RoleType]:
    id_, pass_hash, role = await PostgresQueryExecutor(
        sql=r'SELECT id, pass_hash, role'
            r'  FROM account'
            r' WHERE email = %(email)s',
        email=email, fetch=1,
    ).execute()

    return id_, pass_hash, RoleType(role)


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
