"""Tests for endpoints on the Request & Response API."""
# pylint: disable=redefined-outer-name
# pylint: disable=no-method-argument
# pylint: disable=missing-function-docstring
# pylint: disable=too-few-public-methods

from typing import Tuple

import pytest

from helpers.queue_client import Client, Connection, Channel


# create connection objects and make available for the module scope
connection_and_channel = pytest.mark.usefixtures('connection_and_channel')


@pytest.fixture
def client(
        connection_and_channel: Tuple[Connection, Channel]
) -> Client:
    """Setup an RPC client from test helper module."""

    channel = connection_and_channel[1]

    return Client(channel)


class TestRouteQueueTest:
    """Tests for API endpoint `queue-test`."""

    @staticmethod
    def test_nothing_is_returned(client: Client) -> None:
        """This example is a pretty useless test, instead it should probably
        eventually be paired with a Request via the R&R API to check if the
        side effects from pushing a message on the StS API had the desired
        side effect on the service.

        Such a test would do something like the following:

        1st: Setup initial state
        2nd: Push message via StS API
        3rd: Make R&R again, assert Response changed as expected
        """

        result = client.publish('queue-test', {'a': 1})  # type: ignore

        assert result is None
