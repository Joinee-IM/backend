from unittest.mock import Mock as _Mock
from unittest.mock import AsyncMock as _AsyncMock
from unittest import IsolatedAsyncioTestCase
from unittest import TestCase as _TestCase


class Mock(_Mock):
    def __init__(self, return_value=None, side_effect=None, *args, **kwargs):
        super().__init__(return_value=return_value, side_effect=side_effect, *args, **kwargs)


class AsyncMock(_AsyncMock):
    def __init__(self, return_value=None, side_effect=None, *args, **kwargs):
        super().__init__(return_value=return_value, side_effect=side_effect, *args, **kwargs)


class AsyncTestCase(IsolatedAsyncioTestCase):
    context = {'request_uuid': 'test_uuid'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestCase(_TestCase):
    context = {'request_uuid': 'test_uuid'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
