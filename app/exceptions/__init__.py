class NotFound(Exception):
    """
    Not found
    """


class UniqueViolationError(Exception):
    """
    Unique Violation Error
    """


class LoginExpired(Exception):
    """
    Login token expired
    """


class LoginFailed(Exception):
    """
    Login failed
    """


class NoPermission(Exception):
    """
    No access to resource
    """


class UsernameExists(Exception):
    """
    duplicate username
    """


class IllegalInput(Exception):
    """
    Input is not legal
    """
