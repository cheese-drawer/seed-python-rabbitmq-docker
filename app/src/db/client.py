"""Wrapper on aiopg to simplify connecting to & interacting with db."""

from __future__ import annotations
from typing import Any, List

import aiopg  # type: ignore

from .connection import ConnectionParameters, connect


class Client:
    """Class to manage database connection & expose necessary methods to user.

    Stores connection parameters on init, then exposes methods to
    asynchronously connect & disconnect the database, as well as execute SQL
    queries.
    """

    _connection_params: ConnectionParameters
    _connection: aiopg.Connection
    _cursor: aiopg.Cursor

    def __init__(self, connection_params: ConnectionParameters) -> None:
        self._connection_params = connection_params

    async def connect(self) -> None:
        """Connect to the database."""
        self._connection = await connect(self._connection_params)
        self._cursor = await self._connection.cursor()

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        await self._connection.close()
        await self._cursor.close()

    async def execute(self, query: str) -> List[Any]:
        """Execute the given SQL query.

        Arguments:
            query (str) -- the SQL query to execute

        Returns:
            A List containing all the rows that matched the query.
        """
        result = []
        await self._cursor.execute(query)

        async for row in self._cursor:
            result.append(row)

        return result
