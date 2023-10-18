from datetime import datetime

from starlette_context import context

from security import AuthedAccount
from base import mcs


class Request(metaclass=mcs.Singleton):
    _context = context

    @property
    def account(self) -> AuthedAccount:
        return self._context.get('account')

    @property
    def time(self) -> datetime:
        return self._context.get('time')

    @property
    def uuid(self):
        return self._context.get('request-uuid')


request = Request()
