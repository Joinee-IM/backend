from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
from freezegun import freeze_time

import app.exceptions as exc
from app.base.enums import RoleType
from app.utils import security
from tests import Mock, TestCase


class TestEncodeJWT(TestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.expire = timedelta(seconds=1)
        self.role = RoleType.normal

    @freeze_time('2023-10-25')
    @patch('app.utils.security._jwt_encoder', new_callable=Mock)
    def test_happy_path(self, mock_encoder: Mock):
        mock_encoder.return_value = 'mock-token'
        result = security.encode_jwt(account_id=self.account_id, role=self.role, expire=self.expire)

        self.assertEqual(result, 'mock-token')
        mock_encoder.assert_called_with({
            'account_id': self.account_id,
            'expire': '2023-10-25T00:00:01',
            'role': self.role,
        })


class TestDecodeJWT(TestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.role = RoleType.normal
        self.expire = timedelta(seconds=1)
        self.decoded = {
            'account_id': self.account_id,
            'expire': '2023-10-25T00:00:01',
            'role': self.role,
        }
        self.request_time = datetime(2023, 10, 25)
        self.late_request_time = datetime(2023, 10, 26)
        self.expect_output = security.AuthedAccount(
            id=self.account_id,
            time=self.request_time,
            role=self.role,
        )

    @freeze_time('2023-10-25')
    @patch('app.utils.security._jwt_decoder', new_callable=Mock)
    def test_happy_path(self, mock_decoder: Mock):
        mock_decoder.return_value = self.decoded
        result = security.decode_jwt('encoded', self.request_time)
        mock_decoder.assert_called_with('encoded')
        self.assertEqual(result, self.expect_output)

    @freeze_time('2023-10-25')
    @patch('app.utils.security._jwt_decoder', new_callable=Mock)
    def test_decode_error(self, mock_decoder: Mock):
        with self.assertRaises(exc.LoginExpired):
            mock_decoder.side_effect = jwt.DecodeError
            security.decode_jwt('encoded', self.request_time)

    @freeze_time('2023-10-25')
    @patch('app.utils.security._jwt_decoder', new_callable=Mock)
    def test_login_expire(self, mock_decoder: Mock):
        with self.assertRaises(exc.LoginExpired):
            mock_decoder.return_value = self.decoded
            security.decode_jwt('encoded', self.late_request_time)


class TestHashPasswordService(TestCase):
    def setUp(self) -> None:
        self.password = 'password'

    def test_happy_path(self):
        hash_ = security.hash_password(self.password)
        self.assertTrue(security.verify_password(self.password, hash_))
