"""Shared fixtures for integrated tests."""

from typing import Any, Generator, Tuple
import pytest

from helpers.connection import connect, Connection, Channel


@pytest.fixture(scope="module")
def connection_and_channel(
) -> Generator[Tuple[Connection, Channel], Any, Any]:
    """Set up & tears down a connection to the test broker."""
    connection, channel = connect(
        host='localhost',
        port=8672,
        user='test',
        password='pass'
    )

    yield connection, channel

    connection.close()
