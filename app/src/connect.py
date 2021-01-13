"""
Simplify connecting to the RabbitMQ broker

Opinionated package only sets up one kind of exchange
& only returns ??
"""

from __future__ import annotations
from typing import Callable, Optional
import os
import pika

from dotenv import load_dotenv

# load environment variables from secrets
load_dotenv(os.path.abspath('app/.secrets'))

# setup broker credentials using secrets or defaults
_BROKER_HOST = os.getenv('BROKER_HOST', 'localhost')
_BROKER_PORT = os.getenv('BROKER_PORT', '5672')
_BROKER_USER = os.getenv('BROKER_USER', 'guest')
_BROKER_PASS = os.getenv('BROKER_PASS', 'guest')
_BROKER_EXCHANGE_NAME = os.getenv('BROKER_EXCHANGE_NAME', '')


class Messenger:
    def __init__(
        self,
        host: str = _BROKER_HOST,
        port: int = int(_BROKER_PORT),
        user: str = _BROKER_USER,
        password: str = _BROKER_PASS,
    ):
        credentials = pika.PlainCredentials(user, password)
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host='/',
            credentials=credentials,
        )

        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()

        self._channel.exchange_declare(
            exchange=_BROKER_EXCHANGE_NAME,
            exchange_type='topic'
        )

    def close(self) -> None:
        return self._connection.close()


class Producer(Messenger):
    def send(self, message: str, topic: str = '') -> Producer:
        self._channel.basic_publish(
            exchange=_BROKER_EXCHANGE_NAME,
            routing_key=topic,
            body=message.encode('UTF8')
        )

        return self

    def send_once(self, message: str, topic: str = '') -> None:
        return self.send(message, topic).close()


class Consumer(Messenger):
    def __init__(
        self,
        host: str = _BROKER_HOST,
        port: int = int(_BROKER_PORT),
        user: str = _BROKER_USER,
        password: str = _BROKER_PASS,
    ):
        super().__init__(host=host, port=port, user=user, password=password)

        queue = self._channel.queue_declare(queue='', exclusive=True)
        self._queue_name = queue.method.queue or ''

    def queue_bind(self, topic: str) -> Consumer:
        self._channel.queue_bind(
            exchange=_BROKER_EXCHANGE_NAME,
            queue=self._queue_name,
            routing_key=topic,
        )

        return self

    def consume(self, on_consume: Callable[[str, str], None]):
        def handler(channel, method, _, body):
            on_consume(body.decode(), method.routing_key)

            channel.basic_ack(delivery_tag=method.delivery_tag)

        self._channel.basic_consume(
            queue='',
            on_message_callback=handler,
        )

        self._channel.start_consuming()
