"""Tests for endpoints on the Request & Response API."""
# pylint: disable=missing-function-docstring

from typing import Any, Callable, Tuple, Dict

# import pytest
import unittest
from unittest import TestCase

from helpers.connection import connect, Connection
from helpers.rpc_client import Client


connection: Connection
client: Client


def setUpModule() -> None:
    """Establish connection & create AMQP client."""
    # pylint: disable=global-statement
    # pylint: disable=invalid-name
    global connection
    global client

    connection, channel = connect(
        host='localhost',
        port=8672,
        user='test',
        password='pass'
    )
    client = Client(connection, channel)


def tearDownModule() -> None:
    """Close connection."""
    # pylint: disable=global-statement
    # pylint: disable=invalid-name
    global connection
    connection.close()


class TestRouteTest(TestCase):
    """Tests for API endpoint `test`."""

    def test_response_should_be_successful(self) -> None:
        successful = client.call('test', 'message')['success']

        self.assertTrue(successful)

    def test_response_appends_that_took_forever_to_message(
        self
    ) -> None:
        print('running test_response_appends_that_took_forever_to_message')
        data = client.call('test', 'message')['data']

        self.assertEqual(data, 'message that took forever')


class TestRouteWillError(TestCase):
    """Tests for API endpoint `will-error`."""
    response: Dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.response = client.call('will-error', '')

    def test_response_should_not_be_successful(self) -> None:
        successful = self.response['success']

        self.assertFalse(successful)

    def test_response_should_include_error_information(self) -> None:
        self.assertIn('error', self.response)

    def test_error_data_includes_message(self) -> None:
        message = client.call('will-error', 'message')['error']['message']

        for phrase in ['Just an exception', 'message']:
            # Using `self.subTest` as context allows for more elegance when
            # making multiple assertions in the same test. Instead of stopping
            # test execution if an assertion fails, it records the failure &
            # continues to make the remaining assertions.
            with self.subTest():
                self.assertIn(phrase, message)

    def test_error_data_includes_error_type(self) -> None:
        errtype = self.response['error']['type']

        self.assertEqual(errtype, 'Exception')


class TestRouteDictionary(TestCase):
    """Tests for API endpoint `dictionary`"""

    def test_response_should_include_original_dicts_attributes(
        self
    ) -> None:
        message = {
            'dictionary': 'foo'
        }
        response = client.call('dictionary', message)

        print(response)

        self.assertIn('dictionary', response['data'])

    def test_response_should_include_new_bar_attribute_with_value_baz(
        self
    ) -> None:
        message = {
            'dictionary': 'foo'
        }
        response = client.call('dictionary', message)

        print(response)

        self.assertEqual('baz', response['data']['bar'])


if __name__ == '__main__':
    unittest.main()
