from tests import Mock, TestCase
import app.const as const
import app.utils.invitation_code as invitation_code


class TestGenerate(TestCase):
    def setUp(self) -> None:
        pass

    def test_happy_path(self):
        code = invitation_code.generate()
        self.assertEqual(len(code), const.INVITE_CODE_LENGTH)
        self.assertTrue(all([c in const.AVAILABLE_CODE_CHAR for c in code]))
