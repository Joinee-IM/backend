import abc
import collections
import itertools
import typing

import asyncpg

import app.exceptions as exc
import app.log as log

from . import pg_pool_handler


class QueryExecutor:
    UNIQUE_VIOLATION_ERROR = Exception

    def __init__(
        self, sql: str, parameters: dict[str, any] = None,
        **params,
    ):
        self.sql, self.params = self.format(sql, parameters, **params)

    @staticmethod
    @abc.abstractmethod
    def format(sql: str, parameters: dict[str, any] = None, **params):
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_all(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_one(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def execute(self):
        raise NotImplementedError


class PostgresQueryExecutor(QueryExecutor):
    UNIQUE_VIOLATION_ERROR = asyncpg.exceptions.UniqueViolationError

    @staticmethod
    def format(sql: str, parameters: dict[str, any] = None, **params):
        """
        reference: https://github.com/MagicStack/asyncpg/issues/9#issuecomment-600659015
        """
        named_args = {**params}
        if parameters:
            named_args.update(parameters)
        positional_generator = itertools.count(1)
        positional_map = collections.defaultdict(lambda: '${}'.format(next(positional_generator)))
        formatted_query = sql % positional_map
        positional_items = sorted(
            positional_map.items(),
            key=lambda item: int(item[1].replace('$', '')),
        )
        positional_args = [named_args[named_arg] for named_arg, _ in positional_items]
        log.logger.info((formatted_query, positional_args))
        return formatted_query, positional_args

    async def fetch_all(self):
        try:
            async with pg_pool_handler.cursor() as cursor:
                cursor: asyncpg.connection.Connection
                results = await cursor.fetch(self.sql, *self.params)
            return results
        except exc.UniqueViolationError:
            raise exc.UniqueViolationError

    async def fetch_one(self):
        try:
            async with pg_pool_handler.cursor() as cursor:
                cursor: asyncpg.connection.Connection
                result = await cursor.fetchrow(self.sql, *self.params)
            return result
        except self.UNIQUE_VIOLATION_ERROR:
            raise exc.UniqueViolationError

    async def execute(self):
        try:
            async with pg_pool_handler.cursor() as cursor:
                cursor: asyncpg.connection.Connection
                await cursor.execute(self.sql, *self.params)
        except exc.UniqueViolationError:
            raise exc.UniqueViolationError


def generate_query_parameters(criteria_dict: dict[str, tuple[typing.Any, str]]) -> tuple[list, dict[str: typing.Any]]:
    query = [q for (param_value, q) in criteria_dict.values() if param_value is not None]
    params = {
        param_name: param_value for param_name, (param_value, _) in criteria_dict.items() if
        param_value is not None
    }
    return query, params
