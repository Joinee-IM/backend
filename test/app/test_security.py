from datetime import datetime, timedelta
from test import Mock, TestCase
from unittest.mock import patch

import jwt
from freezegun import freeze_time

import app.exceptions as exc
from app import security
from app.base.enums import RoleType


class TestEncodeJWT(TestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.role = RoleType.normal
        self.expire = timedelta(seconds=1)

    @freeze_time('2023-10-25')
    @patch('app.security._jwt_encoder', new_callable=Mock)
    def test_happy_path(self, mock_encoder: Mock):
        mock_encoder.return_value = 'mock-token'
        result = security.encode_jwt(self.account_id, self.role, self.expire)

        self.assertEqual(result, 'mock-token')
        mock_encoder.assert_called_with({
            'account_id': self.account_id,
            'role': self.role.value,
            'expire': '2023-10-25T00:00:01',
        })


class TestDecodeJWT(TestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.role = RoleType.normal
        self.expire = timedelta(seconds=1)
        self.decoded = {
            'account_id': self.account_id,
            'role': self.role.value,
            'expire': '2023-10-25T00:00:01',
        }
        self.request_time = datetime(2023, 10, 25)
        self.late_request_time = datetime(2023, 10, 26)
        self.expect_output = security.AuthedAccount(
            id=self.account_id,
            time=self.request_time,
        )

    @freeze_time('2023-10-25')
    @patch('app.security._jwt_decoder', new_callable=Mock)
    def test_happy_path(self, mock_decoder: Mock):
        mock_decoder.return_value = self.decoded
        result = security.decode_jwt('encoded', self.request_time)
        mock_decoder.assert_called_with('encoded')
        self.assertEqual(result, self.expect_output)

    @freeze_time('2023-10-25')
    @patch('app.security._jwt_decoder', new_callable=Mock)
    def test_decode_error(self, mock_decoder: Mock):
        with self.assertRaises(exc.LoginExpired):
            mock_decoder.side_effect = jwt.DecodeError
            security.decode_jwt('encoded', self.request_time)

    @freeze_time('2023-10-25')
    @patch('app.security._jwt_decoder', new_callable=Mock)
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
