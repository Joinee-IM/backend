from typing import Sequence

import app.exceptions as exc
from app.base import do
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
)


async def read(court_id: int, include_unpublished: bool = False) -> do.Court:
    try:
        id_, venue_id, number, is_published = await PostgresQueryExecutor(
            sql=fr'SELECT id, venue_id, number, is_published'
                fr'  FROM court'
                fr' WHERE id = %(court_id)s'
                fr'{" AND is_published = True" if not include_unpublished else ""}',
            court_id=court_id,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return do.Court(id=id_, venue_id=venue_id, number=number, is_published=is_published)


async def browse(venue_id: int, include_unpublished: bool = False) -> Sequence[do.Court]:
    results = await PostgresQueryExecutor(
        sql=fr'SELECT id, venue_id, number, is_published'
            fr'  FROM court'
            fr' WHERE venue_id = %(venue_id)s'
            fr'{" AND is_published = True" if not include_unpublished else ""}',
        venue_id=venue_id,
    ).fetch_all()

    return [
        do.Court(
            id=id_,
            venue_id=venue_id,
            number=number,
            is_published=is_published,
        )
        for id_, venue_id, number, is_published in results
    ]


async def edit(
        court_id: int,
        is_published: bool | None = None,
):
    criteria_dict = {
        'is_published': (is_published, 'is_published = %(is_published)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)
    set_sql = ', '.join(query)

    if not set_sql:
        return

    await PostgresQueryExecutor(
        sql=fr'UPDATE court'
            fr'   SET {set_sql}'
            fr' WHERE id = %(court_id)s',
        court_id=court_id, **params,
    ).execute()


async def batch_add(venue_id: int, add: int, start_from: int):
    numbers = range(start_from, start_from + add)
    value_sql = ', '.join(f'(%(venue_id)s, %(number_{i})s, %(is_published)s)' for i, _ in enumerate(numbers))
    params = {f'number_{i}': number for i, number in enumerate(numbers)}
    await PostgresQueryExecutor(
        sql=fr'INSERT INTO court'
            fr'            (venue_id, number, is_published)'
            fr'     VALUES {value_sql}',
        venue_id=venue_id, is_published=True, **params,
    ).execute()


async def batch_read(court_ids: Sequence[int], include_unpublished: bool = False) -> Sequence[do.Court]:
    params = {fr'court_id_{i}': uuid for i, uuid in enumerate(court_ids)}
    in_sql = ', '.join([fr'%({param})s' for param in params])

    results = await PostgresQueryExecutor(
        sql=fr'SELECT id, venue_id, number, is_published'
            fr'  FROM court'
            fr' WHERE venue_id IN ({in_sql})'
            fr'{" AND is_published = True" if not include_unpublished else ""}',
        **params,
    ).fetch_all()

    return [
        do.Court(
            id=id_,
            venue_id=venue_id,
            number=number,
            is_published=is_published,
        )
        for id_, venue_id, number, is_published in results
    ]


async def batch_edit(
        court_ids: Sequence[int],
        is_published: bool | None = None,
) -> None:
    params = {fr'court_id_{i}': uuid for i, uuid in enumerate(court_ids)}
    in_sql = ', '.join([fr'%({param})s' for param in params])

    await PostgresQueryExecutor(
        sql=fr'UPDATE court'
            fr'   SET is_published = %(is_published)s'
            fr' WHERE id IN ({in_sql})',
        is_published=is_published, **params,
    ).execute()
