from typing import Sequence

import asyncpg

import app.exceptions as exc
from app.base import do, enums
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
    pg_pool_handler,
)


async def batch_add(reservation_id: int, member_ids: Sequence[int], manager_id: int | None = None) -> None:
    value_sql = ', '.join(f'(%(reservation_id)s, %(account_id_{i})s, %(is_manager_{i})s, %(is_joined)s)' for i, _ in enumerate(member_ids))  # noqa
    params = {f'account_id_{i}': member_id for i, member_id in enumerate(member_ids)}
    params.update({f'is_manager_{i}': member_id == manager_id for i, member_id in enumerate(member_ids)})
    await PostgresQueryExecutor(
        sql=fr'INSERT INTO reservation_member'
            fr'            (reservation_id, account_id, is_manager, status, source)'
            fr'     VALUES {value_sql}',
        reservation_id=reservation_id, is_joined=False, **params,
    ).execute()


async def batch_add_with_do(members: Sequence[do.ReservationMember]) -> None:
    value_sql = ', '.join(
        f'(%(reservation_id_{i})s, %(account_id_{i})s, %(is_manager_{i})s, %(status_{i})s, %(source_{i})s)'
        for i, _ in enumerate(members)
    )
    params = {}
    for i, member in list(enumerate(members)):
        params.update({
            f'reservation_id_{i}': member.reservation_id,
            f'account_id_{i}': member.account_id,
            f'is_manager_{i}': member.is_manager,
            f'status_{i}': member.status,
            f'source_{i}': member.source,
        })

    await PostgresQueryExecutor(
        sql=fr'INSERT INTO reservation_member'
            fr'            (reservation_id, account_id, is_manager, status, source)'
            fr'     VALUES {value_sql}',
        **params,
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
        sql=r'SELECT reservation_id, account_id, is_manager, status, source'
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
            status=status,
            source=source,
        ) for reservation_id, account_id, is_manager, status, source in results
    ]


async def leave(reservation_id: int, account_id: int) -> None:
    async with pg_pool_handler.cursor() as cursor:
        cursor: asyncpg.Connection
        is_manager = await cursor.fetchval(
            r'DELETE FROM reservation_member'
            r' WHERE reservation_id = $1'
            r'   AND account_id = $2'
            r' RETURNING is_manager',
            reservation_id, account_id,
        )
        if is_manager:
            await cursor.execute(
                r'WITH tmp_tbl AS ('
                r'  SELECT MIN(account_id) AS account_id'
                r'  FROM reservation_member'
                r'  WHERE reservation_id = $1'
                r')'
                r'UPDATE reservation_member'
                r'   SET is_manager = $2'
                r' WHERE reservation_id = $1'
                r'  AND account_id = (SELECT account_id FROM tmp_tbl)',
                reservation_id, True,
            )


async def reject(reservation_id: int, account_id: int) -> None:
    await PostgresQueryExecutor(
        sql=r"UPDATE reservation_member"
            r"   SET status = %(status)s"
            r" WHERE reservation_id = %(reservation_id)s and account_id = %(account_id)s",
        reservation_id=reservation_id, account_id=account_id, status=enums.ReservationMemberStatus.rejected,
    ).execute()


async def read(reservation_id: int, account_id: int) -> do.ReservationMember:
    reservation_member = await PostgresQueryExecutor(
        sql=r'SELECT reservation_id, account_id, is_manager, status, source'
            r'  FROM reservation_member'
            r' WHERE reservation_id = %(reservation_id)s and account_id = %(account_id)s',
        reservation_id=reservation_id, account_id=account_id,
    ).fetch_one()

    try:
        reservation_id, account_id, is_manager, status, source = reservation_member
    except TypeError:
        raise exc.NotFound

    return do.ReservationMember(
        reservation_id=reservation_id,
        account_id=account_id,
        is_manager=is_manager,
        status=status,
        source=source,
    )
