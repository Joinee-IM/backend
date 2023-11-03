from datetime import datetime
from typing import Optional
from uuid import UUID

import starlette_context

import app.exceptions as exc
from app.base import mcs
from app.security import AuthedAccount


class Context(metaclass=mcs.Singleton):
    _context = starlette_context.context

    CONTEXT_AUTHED_ACCOUNT_KEY = 'AUTHED_ACCOUNT'
    REQUEST_UUID = 'REQUEST_UUID'
    REQUEST_TIME = 'REQUEST_TIME'

    @property
    def account(self) -> AuthedAccount:
        account = self._context.get(self.CONTEXT_AUTHED_ACCOUNT_KEY)
        if not account:
            raise exc.NoPermission
        return account

    def set_account(self, account: AuthedAccount) -> None:
        self._context[self.CONTEXT_AUTHED_ACCOUNT_KEY] = account

    def get_account(self) -> AuthedAccount:
        return self._context.get(self.CONTEXT_AUTHED_ACCOUNT_KEY) if self._context.exists() else None

    @property
    def request_uuid(self) -> UUID:
        return self._context[self.REQUEST_UUID]

    def set_request_uuid(self, request_uuid: UUID) -> None:
        self._context[self.REQUEST_UUID] = request_uuid

    def get_request_uuid(self) -> Optional[UUID]:
        return self._context.get(self.REQUEST_UUID) if self._context.exists() else None

    @property
    def request_time(self) -> datetime:
        return self._context[self.REQUEST_TIME]

    def set_request_time(self, request_time: datetime) -> None:
        self._context[self.REQUEST_TIME] = request_time

    def get_request_time(self) -> Optional[datetime]:
        return self._context.get(self.REQUEST_TIME) if self._context.exists() else None


context = Context()
