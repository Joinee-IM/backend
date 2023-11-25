from datetime import date, datetime, timedelta
from typing import Optional, Sequence

import app.exceptions as exc
from app.base import do, enums, vo
from app.persistence.database.util import (PostgresQueryExecutor,
                                           generate_query_parameters)


async def batch_add(reservation_id: int, member_ids: Sequence[int], manager_id: int | None = None) -> None:
    value_sql = ', '.join(f'(%(reservation_id)s, %(account_id_{i})s, %(is_manager_{i})s, %(is_joined)s)' for i, _ in enumerate(member_ids))  # noqa
    params = {f'account_id_{i}': member_id for i, member_id in enumerate(member_ids)}
    params.update({f'is_manager_{i}': member_id == manager_id for i, member_id in enumerate(member_ids)})
    await PostgresQueryExecutor(
        sql=fr'INSERT INTO reservation_member'
            fr'            (reservation_id, account_id, is_manager, is_joined)'
            fr'     VALUES {value_sql}',
        reservation_id=reservation_id, is_joined=False, **params, fetch=None,
    ).execute()
