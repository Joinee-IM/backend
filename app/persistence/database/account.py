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
