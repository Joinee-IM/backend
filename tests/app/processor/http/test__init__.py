from app.processor.http import register_routers
from tests import Mock, TestCase


class TestRegisterRouters(TestCase):
    def test_happy_path(self):
        app = Mock()
        app.include_router = Mock()
        register_routers(app=app)
        self.assertEqual(app.include_router.call_count, 6)
