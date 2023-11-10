import logging

from fastapi import Request

import app.exceptions as exc
from app.config import app_config
from app.middleware.envelope import middleware
from tests import AsyncMock, AsyncTestCase


class TestMiddleware(AsyncTestCase):
    def setUp(self) -> None:
        self.request = Request({'type': 'http', 'method': 'GET', 'headers': []})
        logging.getLogger(app_config.logger_name).disabled = True

    async def test_happy_path(self):
        call_next = AsyncMock(return_value=None)
        result = await middleware(self.request, call_next)
        self.assertIsNone(result)

    async def test_not_found(self):
        call_next = AsyncMock(side_effect=exc.NotFound)
        result = await middleware(self.request, call_next)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.body, b'{"data":null,"error":"NotFound"}')

    async def test_illegal_input(self):
        call_next = AsyncMock(side_effect=exc.IllegalInput)
        result = await middleware(self.request, call_next)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.body, b'{"data":null,"error":"IllegalInput"}')

    async def test_no_permission(self):
        call_next = AsyncMock(side_effect=exc.NoPermission)
        result = await middleware(self.request, call_next)
        self.assertEqual(result.status_code, 403)
        self.assertEqual(result.body, b'{"data":null,"error":"NoPermission"}')

    async def test_unexpected_error(self):
        call_next = AsyncMock(side_effect=TypeError)
        result = await middleware(self.request, call_next)
        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.body, b'{"data":null,"error":"TypeError"}')
