import datetime
from typing import Annotated

import pydantic
from fastapi import Query


def convert_datetime(value: datetime.datetime):
    converted = value
    # converted = pydantic.datetime_parse.parse_datetime(value)

    if value.tzinfo is not None:
        # Convert to server time
        converted = value.astimezone().replace(tzinfo=None)
    return converted


Limit: int | None = Query(default=None, lt=50, gt=0)
Offset: int | None = Query(default=None, ge=0)
ServerTZDatetime = Annotated[datetime.datetime, pydantic.AfterValidator(convert_datetime)]
