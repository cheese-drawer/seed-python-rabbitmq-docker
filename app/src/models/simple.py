from typing import Any, List

from db.model import ModelData


class SimpleData(ModelData):
    """An example Item."""

    # PENDS python 3.9 support in pylint,
    # ModelData inherits from TypedDict
    # pylint: disable=too-few-public-methods

    string: str
    integer: int
    array: List[Any]