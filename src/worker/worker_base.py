import logging
from typing import Callable, Awaitable, Any, Union

from aio_pika.patterns import RPC, Master
from aio_pika.channel import Channel
from aio_pika.connection import Connection

from .connection import ConnectionParameters


class Worker:
    # property types
    _connection: Connection
    _channel: Channel
    # PENDS python 3.9 support in pylint
    # pylint: disable=unsubscriptable-object
    _worker: Union[RPC, Master]
    _connection_params: ConnectionParameters
    logger: logging.Logger
    worker_name: str
    PATTERN: Any

    def __init__(
            self,
            connection_params: ConnectionParameters):
        self._connection_params = connection_params
        self.logger = logging.getLogger(self.worker_name)

    async def _start(self) -> None:
        pass

    async def _stop(self) -> None:
        """Defers to aio-pika.Connection's close method."""
        self.logger.info('Worker stopping...')
        # having mypy ignore the next line--calling close is necessary to
        # gracefully disconnect from rabbitmq broker, but aio_pika's
        # Connection.close method is untyped, throwing an "Call to untyped
        # function "close" in typed context" error when not ignored in strict
        # mode
        await self._connection.close()  # type: ignore

    async def run(self) -> Callable[[], Awaitable[None]]:
        """Start the RPC Worker.

        Must be called inside an asyncio event loop, such as
        `run_until_complete(run())`.
        """
        await self._start()

        return self._stop
