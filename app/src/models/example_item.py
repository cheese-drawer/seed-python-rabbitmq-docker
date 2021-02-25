"""An example implementation of custom object Model."""

from typing import Any, List, Dict

from psycopg2 import sql

from db_wrapper.model import ModelData, Model, Read, Client


class ExampleItemData(ModelData):
    """An example Item."""

    # PENDS python 3.9 support in pylint,
    # ModelData inherits from TypedDict
    # pylint: disable=too-few-public-methods

    string: str
    integer: int
    json: Dict[str, Any]


class ExampleItemReader(Read[ExampleItemData]):
    """Add custom method to Model.read."""

    async def all_by_string(self, string: str) -> List[ExampleItemData]:
        """Read all rows with matching `string` value."""
        query = sql.SQL(
            'SELECT * '
            'FROM {table} '
            'WHERE string = {string};'
        ).format(
            table=self._table,
            string=sql.Identifier(string)
        )

        result: List[ExampleItemData] = await self \
            ._client.execute_and_return(query)

        return result


class ExampleItem(Model[ExampleItemData]):
    """Build an ExampleItem Model instance."""

    read: ExampleItemReader

    def __init__(self, client: Client) -> None:
        super().__init__(client, 'example_item_table')
        self.read = ExampleItemReader(self.client, self.table)
