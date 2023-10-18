from datetime import datetime
from unittest.mock import patch

from fastapi import Request, Response
from freezegun import freeze_time

from base.enums import RoleType
from middleware.auth import middleware
from util.mock import AsyncTestCase, AsyncMock, Mock
from security import AuthedAccount


class TestMiddleware(AsyncTestCase):
    def setUp(self) -> None:
        self.uuid = 'fad08f83-6ad7-429f-baa6-b1c3abf4991c'
        self.context = AsyncTestCase.context
        self.now = datetime(2023, 10, 18)
        self.request = Request({'type': 'http', 'method': 'GET', 'headers': []})
        self.expect_result = Response(headers={'X-Request-UUID': 'fad08f83-6ad7-429f-baa6-b1c3abf4991c'})
        self.context_expect_result = {'account': None, 'time': self.now, 'request_uuid': self.uuid}

        self.request_with_auth_token = Request({'type': 'http', 'method': 'GET', 'headers': [(b'auth-token', b'token')]})
        self.jwt_result = AuthedAccount(id=1, role=RoleType.role1, time=datetime(2023, 10, 18))
        self.context_expect_result_with_auth_token = {'account': self.jwt_result, 'time': self.now, 'request_uuid': self.uuid}

        self.call_next = AsyncMock(return_value=Response())

    @freeze_time('2023-10-18')
    async def test_without_auth_token(self):
        with (
            patch('middleware.auth.context', self.context) as context,
            patch('uuid.uuid1', Mock(return_value=self.uuid)),
        ):
            result = await middleware(self.request, self.call_next)
            self.assertDictEqual(context, self.context_expect_result)

        self.assertIsInstance(result, Response)
        self.assertDictEqual(dict(result.headers), dict(self.expect_result.headers))

    @freeze_time('2023-10-18')
    async def test_with_auth_token(self):
        with (
            patch('middleware.auth.context', self.context) as context,
            patch('uuid.uuid1', Mock(return_value=self.uuid)),
            patch('security.decode_jwt', Mock(return_value=self.jwt_result))
        ):
            result = await middleware(self.request_with_auth_token, self.call_next)
            self.assertDictEqual(context, self.context_expect_result_with_auth_token)

        self.assertIsInstance(result, Response)
        self.assertDictEqual(dict(result.headers), dict(self.expect_result.headers))
