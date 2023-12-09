from unittest.mock import patch

from fastapi import Request

from app.middleware import logging
from tests import AsyncMock, AsyncTestCase, Mock


class TestMiddleware(AsyncTestCase):
    def setUp(self) -> None:
        self.params = b"{'p': 1}"
        self.path = '/test'
        self.request = Request({
            'type': 'http',
            'method': 'GET',
            'headers': [],
            'path': self.path,
            'query_string': self.params,
        })

    @patch('app.log.info', new_callable=Mock)
    async def test_happy_path(self, mock_info: Mock):
        await logging.middleware(self.request, AsyncMock())

        mock_info.assert_called_with(
            msg=f'{self.request.method} {self.request.url.path}, params: {self.request.query_params},',
            extra={
                'request': {
                    'method': self.request.method,
                    'path': self.request.url.path,
                    'params': self.request.query_params,
                },
            },
        )
