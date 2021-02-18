"""Test helper to handle making RPC requests to an AMPQ broker."""

import gzip
import json
import uuid
from typing import Any

import pika

Connection = pika.BlockingConnection
Channel = pika.BlockingConnection


# pylint: disable=too-few-public-methods
class Client:
    """Set up RPC response consumer with handler & provide request caller."""

    channel: Channel
    connection: Connection
    correlation_id: str
    response: Any

    def __init__(
        self,
        connection: Connection,
        channel: Channel
    ):
        self.connection = connection
        self.channel = channel

        print('declaring response queue')

        result = self.channel.queue_declare(
            queue='', exclusive=True, auto_delete=True)
        self.callback_queue = result.method.queue

        print('listening on response queue')

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True)

    def _on_response(self, _, __, props, body):
        if self.correlation_id == props.correlation_id:
            self.response = json.loads(gzip.decompress(body).decode('UTF8'))
            print(f'Response received {self.response}')

    def call(self, target_queue: str, message: str) -> Any:
        """Send message as RPC Request to given queue & return Response."""
        self.response = None
        self.correlation_id = str(uuid.uuid4())
        message_props = pika.BasicProperties(
            reply_to=self.callback_queue,
            correlation_id=self.correlation_id)

        message_as_dict = {
            'data': message,
        }

        print(f'Sending message {message}')

        self.channel.basic_publish(
            exchange='',
            routing_key=target_queue,
            properties=message_props,
            body=gzip.compress(json.dumps(message_as_dict).encode('UTF8')))

        print('Message sent, waiting for response...')

        while self.response is None:
            self.connection.process_data_events(time_limit=120)

        return self.response
