import typing
import enum

T = typing.TypeVar("T")


class StrEnum(str, enum.Enum):
    pass


class GenderType(StrEnum):
    male = 'MALE'
    femail = 'FEMALE'
    unrevealed = 'UNREVEALED'


class FeeType(StrEnum):
    per_hour = 'PER_HOUR'
    per_person = 'PER_PERSON'
    per_person_per_hour = 'PER_PERSON_PER_HOUR'


class PlaceType(StrEnum):
    stadium = 'STADIUM'
    venue = 'VENUE'


class TechnicalType(StrEnum):
    entry = 'ENTRY'
    intermediate = 'INTERMEDIATE'
    advanced = 'ADVANCED'


class RoleType(StrEnum):
    provider = 'PROVIDER'
    normal = 'NORMAL'
