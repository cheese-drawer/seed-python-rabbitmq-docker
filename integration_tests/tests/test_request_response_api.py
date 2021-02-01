"""Tests for endpoints on the Request & Response API."""
# pylint: disable=redefined-outer-name
# pylint: disable=no-method-argument
# pylint: disable=missing-function-docstring

from typing import Tuple

import pytest

from helpers.rpc_client import Client, Connection, Channel


# create connection objects and make available for the module scope
connection_and_channel = pytest.mark.usefixtures('connection_and_channel')


@pytest.fixture
def client(
    connection_and_channel: Tuple[Connection, Channel]
) -> Client:
    """Setup an RPC client from test helper module."""
    return Client(*connection_and_channel)


class TestRouteTest:
    """Tests for API endpoint `test`."""

    @staticmethod
    def test_response_should_be_successful(client):
        successful = client.call('test', 'message')['success']

        assert successful

    @staticmethod
    def test_response_appends_that_took_forever_to_message(client):
        data = client.call('test', 'message')['data']

        assert data == 'message that took forever'


class TestRouteWillError:
    """Tests for API endpoint `will-error`."""

    @staticmethod
    def test_response_should_not_be_successful(client):
        successful = client.call('will-error', '')['success']

        assert not successful

    @staticmethod
    def test_response_should_include_error_information(client):
        response = client.call('will-error', '')

        assert 'error' in response

    @staticmethod
    def test_error_data_includes_message(client):
        message = client.call('will-error', 'message')['error']['message']

        assert 'Just an exception' in message and 'message' in message

    @staticmethod
    def test_error_data_includes_error_type(client):
        errtype = client.call('will-error', '')['error']['type']

        assert errtype == 'Exception'


class TestRouteFoo:
    """Tests for API endpoint `foo`"""

    @staticmethod
    def test_response_should_include_original_dicts_attributes(client):
        message = {
            'foo': 'bar'
        }
        response = client.call('foo', message)

        print(response)

        assert 'foo' in response['data']

    @staticmethod
    def test_response_should_include_new_bar_attribute_with_value_baz(client):
        message = {
            'foo': 'bar'
        }
        response = client.call('foo', message)

        print(response)

        assert response['data']['bar'] == 'baz'