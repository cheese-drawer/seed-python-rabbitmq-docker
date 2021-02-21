"""Tests for endpoints on the Request & Response API."""
# pylint: disable=redefined-outer-name
# pylint: disable=no-method-argument
# pylint: disable=missing-function-docstring
# pylint: disable=too-few-public-methods

from typing import Any, Generator, Tuple

import pytest

from helpers.connection import connect, Connection, Channel
from helpers.queue_client import Client


# create connection objects and make available for the module scope
# connection_and_channel = pytest.mark.usefixtures('connection_and_channel')


def connection_and_channel(
) -> Tuple[Connection, Channel]:
    """Set up & tears down a connection to the test broker."""
    connection, channel = connect(
        host='localhost',
        port=8672,
        user='test',
        password='pass'
    )

    return connection, channel


@pytest.fixture
def queue_client(
) -> Generator[Client, Any, Any]:
    """Setup a Worker client from test helper module."""

    connection, channel = connection_and_channel()

    yield Client(channel)

    connection.close()


class TestRouteQueueTest:
    """Tests for API endpoint `queue-test`."""

    @staticmethod
    def test_nothing_is_returned(queue_client: Client) -> None:
        """This example is a pretty useless test, instead it should probably
        eventually be paired with a Request via the R&R API to check if the
        side effects from pushing a message on the StS API had the desired
        side effect on the service.

        Such a test would do something like the following:

        1st: Setup initial state
        2nd: Push message via StS API
        3rd: Make R&R again, assert Response changed as expected
        """

        result = queue_client.publish('queue-test', {'a': 1})  # type: ignore

        assert result is None
