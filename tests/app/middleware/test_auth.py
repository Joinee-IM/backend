from datetime import datetime
from unittest.mock import patch

from fastapi import Request, Response
from freezegun import freeze_time

from app.base.enums import RoleType
from app.config import AppConfig
from app.middleware.auth import middleware
from app.utils.security import AuthedAccount
from tests import AsyncMock, AsyncTestCase, Mock


class MockAppConfig(AppConfig):
    def __init__(self):
        self.title = 'title'
        self.docs_url = 'docs'
        self.redoc_url = None
        self.logger_name = None
        self.allow_origins = ['abc', 'cde']


class TestMiddleware(AsyncTestCase):
    def setUp(self) -> None:
        self.uuid = 'fad08f83-6ad7-429f-baa6-b1c3abf4991c'
        self.context = AsyncTestCase.context
        self.now = datetime(2023, 10, 18)
        self.request = Request({'type': 'http', 'method': 'GET', 'headers': [(b'origin', b'http://localhost:3000')]})
        self.expect_result = Response(
            headers={
                'X-Request-UUID': 'fad08f83-6ad7-429f-baa6-b1c3abf4991c',
                'Access-Control-Allow-Origin': 'http://localhost:3000',
                'Access-Control-Allow-Credentials': 'true',
            },
        )
        self.context_expect_result = {'REQUEST_TIME': self.now, 'REQUEST_UUID': self.uuid}

        self.request_with_auth_token = Request(
            {
                'type': 'http', 'method': 'GET',
                'headers': [(b'auth-token', b'token'), (b'origin', b'http://localhost:3000')],
            },
        )
        self.jwt_result = AuthedAccount(id=1, time=datetime(2023, 10, 18), role=RoleType.normal)
        self.context_expect_result_with_auth_token = {
            'REQUEST_TIME': self.now,
            'REQUEST_UUID': self.uuid,
        }

        self.call_next = AsyncMock(return_value=Response())

    @freeze_time('2023-10-18')
    async def test_without_auth_token(self):
        with (
            patch('app.middleware.auth.context', self.context) as context,
            patch('uuid.uuid1', Mock(return_value=self.uuid)),
        ):
            result = await middleware(self.request, self.call_next)
            self.assertDictEqual(context._context, self.context_expect_result)

        self.assertIsInstance(result, Response)
        self.assertDictEqual(dict(result.headers), dict(self.expect_result.headers))

    @freeze_time('2023-10-18')
    async def test_with_auth_token(self):
        with (
            patch('app.middleware.auth.context', self.context) as context,
            patch('uuid.uuid1', Mock(return_value=self.uuid)),
            patch('app.utils.security.decode_jwt', Mock(return_value=self.jwt_result)),
        ):
            result = await middleware(self.request_with_auth_token, self.call_next)
            self.assertDictEqual(context._context, self.context_expect_result_with_auth_token)

        self.assertIsInstance(result, Response)
        self.assertDictEqual(dict(result.headers), dict(self.expect_result.headers))
