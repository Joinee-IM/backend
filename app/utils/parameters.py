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


Limit: int = Query(default=10, lt=50, gt=0)
Offset: int = Query(default=0, ge=0)
ServerTZDatetime = Annotated[datetime.datetime, pydantic.AfterValidator(convert_datetime)]
