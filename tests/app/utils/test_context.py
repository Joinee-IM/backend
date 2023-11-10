from datetime import datetime

import app.exceptions as exc
from app.utils.context import Context
from app.utils.security import AuthedAccount
from tests import TestCase


class MockStarletteContext:
    def __init__(self):
        self.context = {}

    def exists(self):
        return True

    def __getitem__(self, item):
        return self.context[item]

    def get(self, item):
        return self.context.get(item)

    def __setitem__(self, key, value):
        self.context[key] = value


class MockContext(Context):
    _context = MockStarletteContext()


class TestContext(TestCase):
    def setUp(self) -> None:
        self.context = MockContext()
        self.authed_account = AuthedAccount(
            id=1,
            time=datetime(2023, 10, 27),
        )
        self.request_time = datetime(2023, 10, 27)
        self.request_uuid = TestCase.context.request_uuid

    def test_account(self):
        self.context.set_account(self.authed_account)
        self.assertEqual(self.context.get_account(), self.authed_account)

    def test_no_account(self):
        self.context.set_account(None)  # noqa
        with self.assertRaises(exc.NoPermission):
            _ = self.context.account

    def test_request_time(self):
        self.context.set_request_time(self.request_time)
        self.assertEqual(self.context.get_request_time(), self.request_time)
        self.assertEqual(self.context.request_time, self.request_time)

    def test_request_uuid(self):
        self.context.set_request_uuid(self.request_uuid)
        self.assertEqual(self.context.get_request_uuid(), self.request_uuid)
