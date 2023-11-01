import typing

import pydantic

T = typing.TypeVar('T')


class Response(pydantic.BaseModel, typing.Generic[T]):
    data: T | None = None
    error: str | None = None
