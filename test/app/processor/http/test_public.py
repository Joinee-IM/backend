from app.processor.http import public
from app.utils import Response
from test import AsyncTestCase


class TestDefaultPage(AsyncTestCase):
    def setUp(self) -> None:
        self.expect_result = '<a href="/docs">/docs</a>'

    async def test_happy_path(self):
        result = await public.default_page()
        self.assertEqual(result, self.expect_result)


class TestHealthCheck(AsyncTestCase):
    def setUp(self) -> None:
        self.expect_result = Response(data=public.HealthCheckOutput())

    async def test_happy_path(self):
        result = await public.health_check()
        self.assertEqual(result.data.health, self.expect_result.data.health)
