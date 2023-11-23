class AckException(Exception):
    """
    Base exception class, represents that the error is acked by the server.
    """
    status_code: int = 400


class NotFound(AckException):
    """
    Not found
    """
    status_code = 404


class UniqueViolationError(AckException):
    """
    Unique Violation Error
    """
    status_code = 409


class LoginExpired(AckException):
    """
    Login token expired
    """
    status_code = 401


class LoginFailed(AckException):
    """
    Login failed
    """
    status_code = 401


class NoPermission(AckException):
    """
    No access to resource
    """
    status_code = 403


class EmailExists(AckException):
    """
    duplicate email
    """
    status_code = 200


class IllegalInput(AckException):
    """
    Input is not legal
    """
    status_code = 422


class CourtReserved(AckException):
    """
    Court is already reserved
    """
