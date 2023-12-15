from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import const, exceptions
from tests import TestCase


class TestLoginFailedExceptionHandler(TestCase):
    def setUp(self):
        self.empty_request = Request(scope={'type': 'http'})
        self.login_failed_expect_response = JSONResponse(
            status_code=401,
            content={'data': None, 'error': 'LoginFailed'},
        )
        self.login_failed_expect_response.delete_cookie(const.COOKIE_ACCOUNT_KEY)
        self.login_failed_expect_response.delete_cookie(const.COOKIE_ROLE_KEY)
        self.login_failed_expect_response.delete_cookie(const.COOKIE_TOKEN_KEY)

    def test_happy_path_login_failed(self):
        result = exceptions.login_failed_exception_handler(self.empty_request, exceptions.LoginFailed())
        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(len(result.headers), 5)

    def test_happy_path_login_expired(self):
        result = exceptions.login_failed_exception_handler(self.empty_request, exceptions.LoginExpired())
        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(len(result.headers), 5)


class TestAckExceptionHandler(TestCase):
    def setUp(self):
        self.empty_request = Request(scope={'type': 'http'})
        self.not_found_expect_response = JSONResponse(
            status_code=404,
            content={'data': None, 'error': 'NotFound'},
        )

    def test_happy_path_not_found(self):
        result = exceptions.ack_exception_handler(self.empty_request, exceptions.NotFound())
        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(len(result.headers), 2)


class TestGeneralExceptionHandler(TestCase):
    def setUp(self):
        self.empty_request = Request(scope={'type': 'http'})
        self.type_error_expect_response = JSONResponse(
            status_code=500,
            content={'data': None, 'error': 'TypeError'},
        )

    def test_happy_path_type_error(self):
        result = exceptions.general_exception_handler(self.empty_request, TypeError())
        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 500)
        self.assertEqual(len(result.headers), 2)


class TestValidationExceptionHandler(TestCase):
    def setUp(self):
        self.empty_request = Request(scope={'type': 'http'})
        self.not_found_expect_response = JSONResponse(
            status_code=422,
            content={'data': None, 'error': 'IllegalInput'},
        )

    def test_happy_path_illegal_input(self):
        result = exceptions.validation_exception_handler(self.empty_request, RequestValidationError([]))
        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(len(result.headers), 2)
