"""Wrapper on aiopg to simplify connecting to & interacting with db."""

from __future__ import annotations
from typing import (
    Any,
    TypeVar,
    Union,
    Optional,
    Hashable,
    List,
    Dict)

import aiopg  # type: ignore
from psycopg2.extras import register_uuid
# importing for the sole purpose of re-exporting
# pylint: disable=unused-import
from psycopg2 import sql

from .connection import ConnectionParameters, connect

# add uuid support to psycopg2 & Postgres
register_uuid()


# Generic doesn't need a more descriptive name
# pylint: disable=invalid-name
T = TypeVar('T')

# pylint: disable=unsubscriptable-object
Query = Union[str, sql.Composed]


class Client:
    """Class to manage database connection & expose necessary methods to user.

    Stores connection parameters on init, then exposes methods to
    asynchronously connect & disconnect the database, as well as execute SQL
    queries.
    """

    _connection_params: ConnectionParameters
    _connection: aiopg.Connection

    def __init__(self, connection_params: ConnectionParameters) -> None:
        self._connection_params = connection_params

    async def connect(self) -> None:
        """Connect to the database."""
        self._connection = await connect(self._connection_params)

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        await self._connection.close()

    # PENDS python 3.9 support in pylint
    # pylint: disable=unsubscriptable-object
    @staticmethod
    async def _execute_query(
        cursor: aiopg.Cursor,
        query: Query,
        params: Optional[Dict[Hashable, Any]] = None,
    ) -> None:
        if params:
            await cursor.execute(query, params)
        else:
            await cursor.execute(query)

    # PENDS python 3.9 support in pylint
    # pylint: disable=unsubscriptable-object
    async def execute(
        self,
        query: Query,
        params: Optional[Dict[Hashable, Any]] = None,
    ) -> None:
        """Execute the given SQL query.

        Arguments:
            query (Query)   -- the SQL query to execute
            params (dict)  -- a dictionary of parameters to interpolate when
                              executing the query

        Returns:
            None
        """
        async with self._connection.cursor() as cursor:
            await self._execute_query(cursor, query, params)

    # PENDS python 3.9 support in pylint
    # pylint: disable=unsubscriptable-object
    async def execute_and_return(
        self,
        query: Query,
        params: Optional[Dict[Hashable, Any]] = None,
    ) -> List[T]:
        """Execute the given SQL query & return the result.

        Arguments:
            query (Query)   -- the SQL query to execute
            params (dict)  -- a dictionary of parameters to interpolate when
                              executing the query

        Returns:
            List containing all the rows that matched the query.
        """
        async with self._connection.cursor() as cursor:
            await self._execute_query(cursor, query, params)

            result = []

            async for row in cursor:
                result.append(row)

            return result
