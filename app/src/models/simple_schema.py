from typing import Any, List

from db.model import Schema


class SimpleSchema(Schema):
    """An example Item."""

    # PENDS python 3.9 support in pylint,
    # Schema inherits from TypedDict
    # pylint: disable=too-few-public-methods

    string: str
    integer: int
    array: List[Any]
