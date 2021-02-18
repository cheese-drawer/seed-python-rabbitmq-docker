"""Tests for endpoints on the Request & Response API."""
# pylint: disable=redefined-outer-name
# pylint: disable=no-method-argument
# pylint: disable=missing-function-docstring
# pylint: disable=too-few-public-methods

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
    print('setting up client...')
    return Client(*connection_and_channel)


class TestRouteTest:
    """Tests for API endpoint `test`."""

    @staticmethod
    def test_response_should_be_successful(client: Client) -> None:
        print('running test_response_should_be_successful')

        successful = client.call('test', 'message')['success']

        assert successful

    @staticmethod
    def test_response_appends_that_took_forever_to_message(
            client: Client
    ) -> None:
        print('running test_response_appends_that_took_forever_to_message')

        data = client.call('test', 'message')['data']

        assert data == 'message that took forever'


# class TestRouteWillError:
#     """Tests for API endpoint `will-error`."""
#
#     @staticmethod
#     def test_response_should_not_be_successful(client: Client) -> None:
#         successful = client.call('will-error', '')['success']
#
#         assert not successful
#
#     @staticmethod
#     def test_response_should_include_error_information(client: Client) -> None:
#         response = client.call('will-error', '')
#
#         assert 'error' in response
#
#     @staticmethod
#     def test_error_data_includes_message(client: Client) -> None:
#         message = client.call('will-error', 'message')['error']['message']
#
#         assert 'Just an exception' in message and 'message' in message
#
#     @staticmethod
#     def test_error_data_includes_error_type(client: Client) -> None:
#         errtype = client.call('will-error', '')['error']['type']
#
#         assert errtype == 'Exception'
#
#
# class TestRouteDictionary:
#     """Tests for API endpoint `dictionary`"""
#
#     @staticmethod
#     def test_response_should_include_original_dicts_attributes(
#             client: Client
#     ) -> None:
#         message = {
#             'dictionary': 'bar'
#         }
#         response = client.call('dictionary', message)
#
#         print(response)
#
#         assert 'dictionary' in response['data']
#
#     @staticmethod
#     def test_response_should_include_new_bar_attribute_with_value_baz(
#             client: Client) -> None:
#         message = {
#             'dictionary': 'bar'
#         }
#         response = client.call('dictionary', message)
#
#         print(response)
#
#         assert response['data']['bar'] == 'baz'
