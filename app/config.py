from datetime import timedelta
import os

from dotenv import dotenv_values

env_values = {
    **dotenv_values(".env"),
    **os.environ,
}


class PGConfig:
    host = env_values.get('PG_HOST')
    port = env_values.get('PG_PORT')
    username = env_values.get('PG_USERNAME')
    password = env_values.get('PG_PASSWORD')
    db_name = env_values.get('PG_DBNAME')
    max_pool_size = int(env_values.get('PG_MAX_POOL_SIZE') or 1)


class AppConfig:
    title = env_values.get('APP_TITLE')
    docs_url = env_values.get('APP_DOCS_URL', None)
    redoc_url = env_values.get('APP_REDOC_URL', None)
    logger_name = env_values.get('APP_LOGGER_NAME', None)


class JWTConfig:
    jwt_secret = env_values.get('JWT_SECRET', 'aaa')
    jwt_encode_algorithm = env_values.get('JWT_ENCODE_ALGORITHM', 'HS256')
    login_expire = timedelta(days=float(env_values.get('LOGIN_EXPIRE', '7')))


class RedisConfig:
    url = env_values.get('REDIS_URL')
    max_pool_size = int(env_values.get('REDIS_MAX_POOL_SIZE') or 1)


pg_config = PGConfig()
app_config = AppConfig()
jwt_config = JWTConfig()
redis_config = RedisConfig()
