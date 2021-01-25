from dataclasses import dataclass
from typing import Tuple, Union

from aio_pika.patterns import RPC, Master
from aio_pika.channel import Channel
from aio_pika.connection import Connection
from aio_pika import connect_robust

#
# RabbitMQ Connection helper
#


@dataclass
class ConnectionParameters:
    """Defines connection parameters for aio-pika."""

    host: str
    port: int
    user: str
    password: str


# PENDS python 3.9 support in pylint
# pylint: disable=unsubscriptable-object
async def connect(
    connection_params: ConnectionParameters
) -> Tuple[str, int, Connection, Channel]:
    host = connection_params.host
    port = connection_params.port

    connection: Connection = await connect_robust(
        host=host,
        port=port,
        login=connection_params.user,
        password=connection_params.password)
    channel: Channel = await connection.channel()

    return host, port, connection, channel
