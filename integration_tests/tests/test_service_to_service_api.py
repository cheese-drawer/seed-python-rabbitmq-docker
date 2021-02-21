"""Tests for endpoints on the Request & Response API."""
# pylint: disable=redefined-outer-name
# pylint: disable=no-method-argument
# pylint: disable=missing-function-docstring
# pylint: disable=too-few-public-methods

from typing import Tuple

import pytest

from helpers.connection import Connection, Channel
from helpers.queue_client import Client as QueueClient
from helpers.rpc_client import Client as RPCClient


# create connection objects and make available for the module scope
connection_and_channel = pytest.mark.usefixtures('connection_and_channel')


@pytest.fixture
def queue_client(
        connection_and_channel: Tuple[Connection, Channel]
) -> QueueClient:
    """Setup a Worker client from test helper module."""

    channel = connection_and_channel[1]

    return QueueClient(channel)


@pytest.fixture
def rpc_client(
    connection_and_channel: Tuple[Connection, Channel]
) -> RPCClient:
    """Setup an RPC client from test helper module."""
    print('setting up client...')
    return RPCClient(*connection_and_channel)


class TestRouteQueueTest:
    """Tests for API endpoint `queue-test`."""

    @staticmethod
    def test_nothing_is_returned(queue_client: QueueClient) -> None:
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


class TestRouteTest:
    """Tests for API endpoint `test`."""

    @staticmethod
    def test_response_should_be_successful(rpc_client: RPCClient) -> None:
        print('running test_response_should_be_successful')

        successful = rpc_client.call('test', 'message')['success']

        assert successful

    @staticmethod
    def test_response_appends_that_took_forever_to_message(
            rpc_client: RPCClient
    ) -> None:
        print('running test_response_appends_that_took_forever_to_message')

        data = rpc_client.call('test', 'message')['data']

        assert data == 'message that took forever'
