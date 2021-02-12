"""Convenience class to simplify database interactions for given interface."""

# std lib dependencies
from __future__ import annotations
from typing import (
    TypeVar,
    Generic,
    Any,
    Tuple,
    List,
    Dict,
    TypedDict
)
from uuid import UUID

# internal dependency
from .client import Client, sql


class Schema(TypedDict):
    """Base interface for Schema to be used in Model."""

    # PENDS python 3.9 support in pylint
    # pylint: disable=inherit-non-class
    # pylint: disable=too-few-public-methods

    _id: UUID


# Generic doesn't need a more descriptive name
# pylint: disable=invalid-name
T = TypeVar('T', bound=Schema)


class UnexpectedMultipleResults(Exception):
    """Raised when query receives multiple results when only one expected."""

    def __init__(self, results: List[Any]) -> None:
        message = 'Multiple results received when only ' \
                  f'one was expected: {results}'
        super().__init__(self, message)


class NoResultFound(Exception):
    """Raised when query receives no results when 1+ results expected."""

    def __init__(self) -> None:
        message = 'No result was found'
        super().__init__(self, message)


# pylint: disable=too-few-public-methods
class Create(Generic[T]):
    """Encapsulate Create operations for Model.read."""

    _client: Client
    _table: sql.Composable

    def __init__(self, client: Client, table: sql.Composable) -> None:
        self._client = client
        self._table = table

    async def one(self, item: T) -> T:
        """Create one new record with a given item."""
        columns: List[sql.Identifier] = []
        values: List[sql.Identifier] = []

        for column, value in item.items():
            if column == '_id':
                values.append(sql.Identifier(str(value)))
            else:
                values.append(sql.Identifier(value))

            columns.append(sql.Identifier(column))

        query = sql.SQL(
            'INSERT INTO {table}({columns}) '
            'VALUES ({values}) '
            'RETURNING *;'
        ).format(
            table=self._table,
            columns=sql.SQL(',').join(columns),
            values=sql.SQL(',').join(values),
        )

        result: List[T] = await self._client.execute_and_return(query)

        return result[0]


class Read(Generic[T]):
    """Encapsulate Read operations for Model.read."""

    _client: Client
    _table: sql.Composable

    def __init__(self, client: Client, table: sql.Composable) -> None:
        self._client = client
        self._table = table

    async def one_by_id(self, id_value: str) -> T:
        """Read a row by it's id."""
        query = sql.SQL(
            'SELECT * '
            'FROM {table} '
            'WHERE id = {id_value};'
        ).format(
            table=self._table,
            id_value=sql.Identifier(id_value)
        )

        result: List[T] = await self._client.execute_and_return(query)

        # Should only return one item from DB
        if len(result) > 1:
            raise UnexpectedMultipleResults(result)
        if len(result) == 0:
            raise NoResultFound()

        return result[0]


class Update(Generic[T]):
    """Encapsulate Update operations for Model.read."""

    _client: Client
    _table: sql.Composable

    def __init__(self, client: Client, table: sql.Composable) -> None:
        self._client = client
        self._table = table

    async def one(self, id_value: str, changes: Dict[str, Any]) -> T:
        """Apply changes to row with given id.

        Arguments:
            id_value (string) - the id of the row to update
            changes (dict)    - a dictionary of changes to apply,
                                matches keys to column names & values to values

        Returns:
            full value of row updated
        """
        def compose_one_change(change: Tuple[str, Any]) -> sql.Composed:
            key = change[0]
            value = change[1]

            return sql.SQL("{key} = {value}").format(
                key=sql.Identifier(key), value=sql.Identifier(value))

        def compose_changes(changes: Dict[str, Any]) -> sql.Composed:
            return sql.SQL(',').join(
                [compose_one_change(change) for change in changes.items()])

        query = sql.SQL(
            'UPDATE {table} '
            'SET {changes} '
            'WHERE id = {id_value} '
            'RETURNING *;'
        ).format(
            table=self._table,
            changes=compose_changes(changes),
            id_value=sql.Identifier(id_value),
        )

        result: List[T] = await self._client.execute_and_return(query)

        return result[0]


class Delete(Generic[T]):
    """Encapsulate Delete operations for Model.read."""

    _client: Client
    _table: sql.Composable

    def __init__(self, client: Client, table: sql.Composable) -> None:
        self._client = client
        self._table = table

    async def one(self, id_value: str) -> T:
        """Delete one record with matching ID."""
        query = sql.SQL(
            'DELETE FROM {table} '
            'WHERE id = {id_value} '
            'RETURNING *;'
        ).format(
            table=self._table,
            id_value=sql.Identifier(id_value)
        )

        result: List[T] = await self._client.execute_and_return(query)

        # Should only return one item from DB
        if len(result) > 1:
            raise UnexpectedMultipleResults(result)
        if len(result) == 0:
            raise NoResultFound()

        return result[0]


class Model(Generic[T]):
    """Class to manage execution of database queries for a model."""

    # Properties don't need docstrings
    # pylint: disable=missing-function-docstring

    client: Client
    table: sql.Identifier

    _create: Create[T]
    _read: Read[T]
    _update: Update[T]
    _delete: Delete[T]

    # PENDS python 3.9 support in pylint
    # pylint: disable=unsubscriptable-object
    def __init__(
        self,
        client: Client, table: str,
    ) -> None:
        self.client = client
        self.table = sql.Identifier(table)

        self._create = Create[T](self.client, self.table)
        self._read = Read[T](self.client, self.table)
        self._update = Update[T](self.client, self.table)
        self._delete = Delete[T](self.client, self.table)

    @property
    def create(self) -> Create[T]:
        """Methods for creating new records of the Model."""
        return self._create

    @create.setter
    def create(self, creator: Create[T]) -> None:
        if isinstance(creator, Create):
            self._create = creator
        else:
            raise TypeError('Model.create must be an instance of Create.')

    @property
    def read(self) -> Read[T]:
        """Methods for reading records of the Model."""
        return self._read

    @read.setter
    def read(self, reader: Read[T]) -> None:
        if isinstance(reader, Read):
            self._read = reader
        else:
            raise TypeError('Model.read must be an instance of Read.')

    @property
    def update(self) -> Update[T]:
        """Methods for updating records of the Model."""
        return self._update

    @update.setter
    def update(self, updater: Update[T]) -> None:
        if isinstance(updater, Update):
            self._update = updater
        else:
            raise TypeError('Model.update must be an instance of Update.')

    @property
    def delete(self) -> Delete[T]:
        """Methods for deleting records of the Model."""
        return self._delete

    @delete.setter
    def delete(self, deleter: Delete[T]) -> None:
        if isinstance(deleter, Delete):
            self._delete = deleter
        else:
            raise TypeError('Model.delete must be an instance of Delete.')
