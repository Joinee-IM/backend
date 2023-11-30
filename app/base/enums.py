import enum
import typing

T = typing.TypeVar('T')


class StrEnum(str, enum.Enum):
    pass


class GenderType(StrEnum):
    male = 'MALE'
    female = 'FEMALE'
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


class Sorter(StrEnum):
    asc = 'ASC'
    desc = 'DESC'


class VenueAvailableSortBy(StrEnum):
    current_user_count = 'CURRENT_USER_COUNT'


class BrowseReservationSortBy(StrEnum):
    vacancy = 'vacancy'
    time = 'time'


class ReservationStatus(StrEnum):
    """
    This status is NOT stored in db,
    instead, it's derived from reservation's `start time`, `end time`, and `is_cancelled`.
    """
    in_progress = 'IN_PROGRESS'
    cancelled = 'CANCELLED'
    finished = 'FINISHED'


class ViewMyReservationSortBy(StrEnum):
    time = 'time'
    stadium_name = 'stadium_name'
    venue_name = 'venue_name'
    is_manager = 'is_manager'
    vacancy = 'vacancy'
    status = 'status'


class ViewProviderStadiumSortBy(StrEnum):
    district_name = 'district_name'
    stadium_name = 'stadium_name'
    venue_count = 'venue_count'
    is_published = 'is_published'


class ViewProviderVenueSortBy(StrEnum):
    stadium_name = 'stadium_name'
    venue_name = 'venue_name'
    court_count = 'court_count'
    area = 'area'
    is_published = 'is_published'
