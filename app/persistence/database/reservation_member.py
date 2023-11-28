from typing import Sequence

from app.base import do
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
        reservation_id=reservation_id, is_joined=False, **params,
    ).execute()


async def browse(
        reservation_id: int | None = None,
        account_id: int | None = None,
) -> Sequence[do.ReservationMember]:

    criteria_dict = {
        'reservation_id': (reservation_id, 'reservation_id = %(reservation_id)s'),
        'account_id': (account_id, 'account_id = %(account_id)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    results = await PostgresQueryExecutor(
        sql=r'SELECT reservation_id, account_id, is_manager, is_joined'
            r'  FROM reservation_member'
            fr' {where_sql}'
            r' ORDER BY is_manager, account_id',
        **params,
    ).fetch_all()

    return [
        do.ReservationMember(
            reservation_id=reservation_id,
            account_id=account_id,
            is_manager=is_manager,
            is_joined=is_joined,
        ) for reservation_id, account_id, is_manager, is_joined in results
    ]
