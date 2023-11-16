import os
from datetime import timedelta
from distutils.util import strtobool

from dotenv import dotenv_values

env_values = {
    **dotenv_values('.env'),
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
    title = env_values.get('APP_TITLE', 'APP_TITLE')
    docs_url = env_values.get('APP_DOCS_URL', None)
    redoc_url = env_values.get('APP_REDOC_URL', None)
    logger_name = env_values.get('APP_LOGGER_NAME', None)
    allow_origins = env_values.get('APP_ALLOW_ORIGINS', '').split(' ')


class JWTConfig:
    jwt_secret = env_values.get('JWT_SECRET', 'aaa')
    jwt_encode_algorithm = env_values.get('JWT_ENCODE_ALGORITHM', 'HS256')
    login_expire = timedelta(days=float(env_values.get('LOGIN_EXPIRE', '7')))


class RedisConfig:
    url = env_values.get('REDIS_URL')
    max_pool_size = int(env_values.get('REDIS_MAX_POOL_SIZE') or 1)


class SMTPConfig:
    host = env_values.get('SMTP_HOST')
    port = env_values.get('SMTP_PORT')
    username = env_values.get('SMTP_USERNAME')
    password = env_values.get('SMTP_PASSWORD')
    use_tls = strtobool(env_values.get('SMTP_USE_TLS', 'false'))


class ServiceConfig:
    domain = env_values.get('SERVICE_DOMAIN')
    port = env_values.get('SERVICE_PORT')
    use_https = bool(strtobool(env_values.get('SERVICE_USE_HTTPS', 'false')))

    @property
    def url(self) -> str:
        protocol = 'https' if self.use_https else 'http'
        port_postfix = f':{self.port}' if self.port else ''
        return f'{protocol}://{self.domain}{port_postfix}'


class GoogleConfig:
    CLIENT_ID = env_values.get('GOOGLE_CLIENT_ID')
    CLIENT_SECRET = env_values.get('GOOGLE_CLIENT_SECRET')
    LOGIN_REDIRECT_URI = env_values.get('GOOGLE_LOGIN_REDIRECT_URI')
    SERVER_URL = env_values.get('GOOGLE_SERVER_URL')
    CLIENT_KWARGS = env_values.get('GOOGLE_CLIENT_KWARGS')


pg_config = PGConfig()
app_config = AppConfig()
jwt_config = JWTConfig()
redis_config = RedisConfig()
smtp_config = SMTPConfig()
service_config = ServiceConfig()
google_config = GoogleConfig()
