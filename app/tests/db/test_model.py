"""Tests for src.db.model.

These tests are limited by mocking of Client's ability to query Postgres. This
means that actual SQL queries aren't being tested, just the processing of any
results received & the act of making a request.
"""
# pylint: disable=redefined-outer-name
# pylint: disable=no-method-argument
# pylint: disable=missing-function-docstring
# pylint: disable=too-few-public-methods

from typing import (
    cast,
    Any,
    TypeVar,
    Generic,
    Iterable,
    List,
    Tuple,
    Dict,
    TypedDict,
)
from uuid import uuid4, UUID
from unittest.mock import MagicMock

import pytest

from src.db.connection import ConnectionParameters
from src.db.client import Client
from src.db.model import (
    Model,
    Schema,
    Read,
    UnexpectedMultipleResults,
    NoResultFound)


class AsyncMock(MagicMock):
    """Extend unittest.mock.MagicMock to allow mocking of async functions."""
    # pylint: disable=invalid-overridden-method
    # pylint: disable=useless-super-delegation

    async def __call__(self, *args, **kwargs):  # type: ignore
        return super().__call__(*args, **kwargs)


def get_client() -> Client:
    """Create a client with placeholder connection data."""
    conn_params = ConnectionParameters('a', 'a', 'a', 'a')
    return Client(conn_params)


# Generic doesn't need a more descriptive name
# pylint: disable=invalid-name
T = TypeVar('T', bound=Schema)


def setup(query_result: List[T]) -> Tuple[Model[T], Client]:
    """Setup helper that returns instances of both a Model & a Client.

    Mocks the execute_and_return method on the Client instance to skip
    normal execution & just return the given query_result.
    """
    client = get_client()

    # mock client's sql execution method
    client.execute_and_return = AsyncMock(  # type:ignore
        return_value=query_result)

    # init model with mocked client
    model = Model[Any](client, 'test')

    return model, client


def composed_to_string(seq: Iterable[Any]) -> str:
    """Test helper to convert a sql query to a string for comparison.

    Works for queries built with postgres.sql.Composable objects.
    From https://github.com/psycopg/psycopg2/issues/747#issuecomment-662857306
    """
    parts = str(seq).split("'")
    return "".join([p for i, p in enumerate(parts) if i % 2 == 1])


class TestRead:
    """Testing Model.read's methods."""

    class TestOneById:
        """Testing Model.read.one_by_id."""

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_correctly_builds_query_with_given_id() -> None:
            item: Schema = {'_id': uuid4()}
            model, client = setup([item])
            await model.read.one_by_id(str(item['_id']))
            query_composed = cast(
                AsyncMock, client.execute_and_return).call_args[0][0]
            query = composed_to_string(query_composed)

            assert query == "SELECT * " \
                            "FROM test " \
                            f"WHERE id = {item['_id']};"

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_returns_a_single_result() -> None:
            item: Schema = {'_id': uuid4()}
            model, _ = setup([item])
            result = await model.read.one_by_id(str(item['_id']))

            assert result == item

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_raises_exception_if_more_than_one_result() -> None:
            item: Schema = {'_id': uuid4()}
            model, _ = setup([item, item])

            # pylint: disable=unused-variable
            with pytest.raises(UnexpectedMultipleResults) as err:
                await model.read.one_by_id(str(item['_id']))

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_raises_exception_if_no_result_to_return() -> None:
            model: Model[Schema]
            model, _ = setup([])

            # pylint: disable=unused-variable
            with pytest.raises(NoResultFound) as err:
                await model.read.one_by_id('id')


class TestCreate:
    """Testing Model.create's methods."""

    class Item(Schema):
        a: str
        b: str

    class TestOne:
        """Testing Model.create.one."""

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_correctly_builds_query_with_given_data() -> None:
            item: TestCreate.Item = {
                '_id': uuid4(),
                'a': 'a',
                'b': 'b',
            }
            model, client = setup([item])

            await model.create.one(item)
            query_composed = cast(
                AsyncMock, client.execute_and_return).call_args[0][0]
            query = composed_to_string(query_composed)

            assert query == 'INSERT INTO test(_id,a,b) ' \
                            f"VALUES ({item['_id']},a,b) " \
                            'RETURNING *;'

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_returns_the_new_record() -> None:
            item: TestCreate.Item = {
                '_id': uuid4(),
                'a': 'a',
                'b': 'b',
            }
            model, _ = setup([item])

            result = await model.create.one(item)

            assert result == item


class TestUpdate:
    """Testing Model.update's methods."""

    class Item(Schema):
        """Example Schema Item for testing."""
        a: str
        b: str

    class TestOne:
        """Testing Model.update.one_by_id."""

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_correctly_builds_query_with_given_data() -> None:
            item: TestUpdate.Item = {
                '_id': uuid4(),
                'a': 'a',
                'b': 'b',
            }
            # cast required to avoid mypy error due to unpacking
            # TypedDict, see more on GitHub issue
            # https://github.com/python/mypy/issues/4122
            updated = cast(TestUpdate.Item, {**item, 'b': 'c'})
            model, client = setup([updated])

            await model.update.one(str(item['_id']), {'b': 'c'})
            query_composed = cast(
                AsyncMock, client.execute_and_return).call_args[0][0]
            query = composed_to_string(query_composed)

            assert query == 'UPDATE test ' \
                            'SET b = c ' \
                            f"WHERE id = {item['_id']} " \
                            'RETURNING *;'

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_returns_the_new_record() -> None:
            item: TestUpdate.Item = {
                '_id': uuid4(),
                'a': 'a',
                'b': 'b',
            }
            # cast required to avoid mypy error due to unpacking
            # TypedDict, see more on GitHub issue
            # https://github.com/python/mypy/issues/4122
            updated = cast(TestUpdate.Item, {**item, 'b': 'c'})
            model, _ = setup([updated])

            result = await model.update.one(str(item['_id']), {'b': 'c'})

            assert result == updated


class TestDelete:
    """Testing Model.delete's methods."""

    class Item(Schema):
        """Example Schema Item for testing."""
        a: str
        b: str

    class TestOneById:
        """Testing Model.update.one_by_id"""

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_correctly_builds_query_with_given_data() -> None:
            item: TestDelete.Item = {
                '_id': uuid4(),
                'a': 'a',
                'b': 'b',
            }
            model, client = setup([item])

            await model.delete.one(str(item['_id']))

            query_composed = cast(
                AsyncMock, client.execute_and_return).call_args[0][0]
            query = composed_to_string(query_composed)

            assert query == 'DELETE FROM test ' \
                            f"WHERE id = {item['_id']} " \
                            'RETURNING *;'

        @staticmethod
        @pytest.mark.asyncio
        async def test_it_returns_the_deleted_record() -> None:
            item: TestDelete.Item = {
                '_id': uuid4(),
                'a': 'a',
                'b': 'b',
            }
            model, _ = setup([item])

            result = await model.delete.one(str(item['_id']))

            assert result == item


class TestModel:
    """Testing Model usage."""

    class TestExtendingModel:
        """Testing Model's extensibility."""

        @staticmethod
        def test_it_can_add_new_queries_by_replacing_a_crud_property() -> None:
            class ReadExtended(Read[T]):
                """Extending Read with additional query."""

                @staticmethod
                def new_query() -> None:
                    pass

            model = Model[T](get_client(), 'test')
            model.read = ReadExtended(model.client, model.table)

            new_method = getattr(model.read, "new_query", None)

            assert new_method and callable(new_method)

        @staticmethod
        def test_it_still_has_original_queries_after_extending() -> None:
            class ReadExtended(Read[T]):
                """Extending Read with additional query."""

                @staticmethod
                def new_query() -> None:
                    pass

            model = Model[T](get_client(), 'test')
            model.read = ReadExtended(model.client, model.table)

            old_method = getattr(model.read, "one_by_id", None)

            assert old_method and callable(old_method)

    class TestDefiningSchema:
        """Testing Model's generic types"""

        @staticmethod
        def test_it_allows_user_to_constrain_accepted_and_returned_types(
        ) -> None:
            # # pylint: disable=inherit-non-class
            # class Data(TypedDict):
            #     """Define an example schema"""
            #     _id: UUID
            #     string: str
            #     integer: int
            #     floating: float
            Data = TypedDict(
                'Data',
                {
                    '_id': UUID,
                    'string': str,
                    'integer': int,
                    'floating': float
                })

            data = Model[Data](get_client(), 'data')
