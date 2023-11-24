from datetime import datetime, timedelta
from functools import partial
from typing import NamedTuple

import jwt
from passlib.hash import argon2

import app.exceptions as exc
from app.config import jwt_config

_jwt_encoder = partial(jwt.encode, key=jwt_config.jwt_secret, algorithm=jwt_config.jwt_encode_algorithm)
_jwt_decoder = partial(jwt.decode, key=jwt_config.jwt_secret, algorithms=[jwt_config.jwt_encode_algorithm])


def encode_jwt(account_id: int, expire: timedelta = jwt_config.login_expire) -> str:
    return _jwt_encoder({
        'account_id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    })


class AuthedAccount(NamedTuple):
    id: int
    time: datetime


def decode_jwt(encoded: str, time: datetime) -> AuthedAccount:
    try:
        decoded = _jwt_decoder(encoded)
    except jwt.DecodeError:
        raise exc.LoginExpired

    expire = datetime.fromisoformat(decoded['expire'])
    if time > expire:
        raise exc.LoginExpired

    account_id = decoded['account_id']
    return AuthedAccount(id=account_id, time=time)


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, pass_hash: str) -> bool:
    return argon2.verify(password, pass_hash)
