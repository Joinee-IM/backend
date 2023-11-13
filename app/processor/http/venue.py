from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import do, enums
from app.utils import Limit, Offset, Response

router = APIRouter(
    tags=['Venue'],
    default_response_class=responses.JSONResponse,
)


class VenueSearchParameters(BaseModel):
    name: str | None = Query(default=None)
    sport_id: int | None = Query(default=None)
    is_reservable: bool | None = Query(default=None)
    sort_by: enums.VenueAvailableSortBy = Query(default=enums.VenueAvailableSortBy.current_user_count)
    order: enums.Sorter = Query(default=enums.Sorter.desc)
    limit: int = Limit
    offset: int = Offset


@router.get('/venue')
async def browse_venue(params: VenueSearchParameters = Depends()) -> Response[Sequence[do.Venue]]:
    venues = await db.venue.browse(
        name=params.name,
        sport_id=params.sport_id,
        is_reservable=params.is_reservable,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )
    return Response(data=venues)
