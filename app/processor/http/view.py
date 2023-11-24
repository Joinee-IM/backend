from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import enums, vo
from app.middleware.headers import get_auth_token
from app.utils import Limit, Offset, Response, context

router = APIRouter(
    tags=['View'],
    default_response_class=responses.JSONResponse,
)


class ViewMyReservationParams(BaseModel):
    account_id: int = Query()
    sort_by: enums.ViewMyReservationSortBy = Query(default=enums.ViewMyReservationSortBy.time)
    order: enums.Sorter = Query(default=enums.Sorter.desc)
    limit: int = Limit
    offset: int = Offset


@router.get('/view/reservation')
async def view_my_reservation(params: ViewMyReservationParams = Depends(), _=Depends(get_auth_token)) -> Response[Sequence[vo.ViewMyReservation]]:
    if context.account.id != params.account_id:
        raise exc.NoPermission

    reservations = await db.view.browse_my_reservation(
        account_id=params.account_id,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )
    return Response(data=reservations)
