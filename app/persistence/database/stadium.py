from typing import Sequence

from app.base import do
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
)


async def browse(
        name: str | None = None,
        city_id: int | None = None,
        district_id: int | None = None,
        sport_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
) -> Sequence[do.Stadium]:
    criteria_dict = {
        'name': (f'%{name}%' if name else None, 'stadium.name LIKE %(name)s'),
        'city_id': (city_id, 'district.city_id = %(city_id)s'),
        'district_id': (district_id, 'district.id = %(district_id)s'),
        'sport_id': (sport_id, 'venue.sport_id = %(sport_id)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    results = await PostgresQueryExecutor(
        sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number,'
            fr'       description, long, lat'
            fr'  FROM stadium'
            fr' INNER JOIN district ON stadium.district_id = district.id'
            fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
            fr' {where_sql}'
            fr' ORDER BY stadium.id'
            fr' LIMIT %(limit)s OFFSET %(offset)s',
        limit=limit, offset=offset, fetch='all', **params,
    ).execute()

    return [
        do.Stadium(
            id=id_,
            name=name,
            district_id=district_id,
            contact_number=contact_number,
            description=description,
            long=long,
            lat=lat,
        ) for id_, name, district_id, contact_number, description, long, lat in results
    ]
