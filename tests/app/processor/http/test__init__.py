from app.processor.http import register_routers
from tests import Mock, TestCase, patch


class TestRegisterRouters(TestCase):
    @patch('app.processor.http.get_openapi', Mock())
    def test_happy_path(self):
        app = Mock()
        app.include_router = Mock()
        app.get = Mock(return_value=Mock())
        register_routers(app=app)
        self.assertEqual(app.include_router.call_count, 13)
        self.assertEqual(app.get.call_count, 2)
