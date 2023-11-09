from unittest import IsolatedAsyncioTestCase
from unittest import TestCase as _TestCase
from unittest.mock import AsyncMock as _AsyncMock
from unittest.mock import Mock as _Mock

from app.utils.context import Context
from app.utils.security import AuthedAccount


class Mock(_Mock):
    def __init__(self, return_value=None, side_effect=None, *args, **kwargs):
        super().__init__(return_value=return_value, side_effect=side_effect, *args, **kwargs)


class AsyncMock(_AsyncMock):
    def __init__(self, return_value=None, side_effect=None, *args, **kwargs):
        super().__init__(return_value=return_value, side_effect=side_effect, *args, **kwargs)


class MockContext(Context):
    _context = {'REQUEST_UUID': 'test_uuid'}

    def reset_context(self):
        self._context = {'REQUEST_UUID': 'test_uuid'}

    def get_request_time(self):
        return self._context.get(self.REQUEST_TIME)

    def get_request_uuid(self):
        return self._context.get(self.REQUEST_UUID)

    def get_account(self) -> AuthedAccount:
        return self._context.get(self.CONTEXT_AUTHED_ACCOUNT_KEY)  # noqa


class AsyncTestCase(IsolatedAsyncioTestCase):
    context = MockContext()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestCase(_TestCase):
    context = MockContext()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
