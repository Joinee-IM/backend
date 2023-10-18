from unittest.mock import Mock as M
from unittest.mock import AsyncMock as AM
from unittest import IsolatedAsyncioTestCase


class Mock(M):
    def __init__(self, return_value=None, side_effect=None, *args, **kwargs):
        super().__init__(return_value=return_value, side_effect=side_effect, *args, **kwargs)


class AsyncMock(AM):
    def __init__(self, return_value = None, side_effect = None,*args, **kwargs):
        super().__init__(return_value=return_value, side_effect=side_effect, *args, **kwargs)


class AsyncTestCase(IsolatedAsyncioTestCase):
    context = {'request_uuid': 'test_uuid'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)