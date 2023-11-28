from typing import Sequence

import app.exceptions as exc
from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def read(court_id: int, include_unpublished: bool = False) -> do.Court:
    try:
        id_, venue_id, is_published = await PostgresQueryExecutor(
            sql=fr'SELECT id, venue_id, is_published'
                fr'  FROM court'
                fr' WHERE id = %(court_id)s'
                fr'{" AND is_published = True" if not include_unpublished else ""}',
            court_id=court_id, fetch=1,
        ).execute()
    except TypeError:
        raise exc.NotFound

    return do.Court(id=id_, venue_id=venue_id, is_published=is_published)


async def browse(venue_id: int, include_unpublished: bool = False) -> Sequence[do.Court]:
    results = await PostgresQueryExecutor(
        sql=fr'SELECT id, venue_id, is_published'
            fr'  FROM court'
            fr' WHERE venue_id = %(venue_id)s'
            fr'{" AND is_published = True" if not include_unpublished else ""}',
        venue_id=venue_id, fetch='all',
    ).fetch_all()

    return [
        do.Court(
            id=id_,
            venue_id=venue_id,
            is_published=is_published
        )
        for id_, venue_id, is_published in results
    ]
