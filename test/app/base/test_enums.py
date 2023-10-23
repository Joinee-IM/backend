from app.base.enums import RoleType
from test import TestCase


class TestRoleType(TestCase):
    def setUp(self) -> None:
        self.small = RoleType.role1
        self.large = RoleType.role2

    def test_greater_than(self):
        self.assertTrue(self.large > self.small)

    def test_less_than(self):
        self.assertTrue(self.small < self.large)

    def test_greater_equal(self):
        self.assertTrue(self.large >= self.small)

    def test_less_equal(self):
        self.assertTrue(self.small <= self.large)