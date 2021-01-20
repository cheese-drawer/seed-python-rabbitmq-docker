"""
Classes for making working with RabbitMQ RPC workers easier.

Powered by aio-pika.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass
import gzip
import json
import os
import logging
import traceback
from typing import cast, Any, Awaitable, Callable, List, TypedDict
from mypy_extensions import NamedArg

from aio_pika.patterns import RPC
from aio_pika.channel import Channel
from aio_pika.connection import Connection
from aio_pika import connect_robust
from dotenv import load_dotenv


load_dotenv(os.path.abspath('app/.secrets'))


#
# aio_pika.RPC overloads
#

DEFAULT_EXCHANGE_NAME = os.getenv('BROKER_EXCHANGE_NAME', RPC.DLX_NAME)
print(f'default exchange name: {DEFAULT_EXCHANGE_NAME}')


class CustomJsonGzipRPC(RPC):
    """Extend RPC pattern to automate serializing & compressing
    messages as JSON with Gzip.
    """

    # override default exchange name in aio_pika.patterns.rpc.RPC
    # has to be done via environment variable to avoid complex
    # changes to RPC's __init__ or create methods
    DLX_NAME = DEFAULT_EXCHANGE_NAME

    SERIALIZER = json
    CONTENT_TYPE = 'application/octet-stream'

    def serialize(self, data: Any) -> bytes:
        return gzip.compress(
            self.SERIALIZER.dumps(
                data,
                ensure_ascii=False,
                default=repr).encode('UTF8'))

    def serialize_exception(self, exception: Exception) -> bytes:
        return self.serialize({
            'ok': False,
            'error': {
                'type': exception.__class__.__name__,
                'message': repr(exception),
                'args': exception.args,
                'trace': ''.join(
                    traceback.format_exception(
                        etype=type(exception),
                        value=exception,
                        tb=exception.__traceback__)),
            },
        })

    def deserialize(self, data: Any) -> bytes:
        return super().deserialize(gzip.decompress(data))


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


#
# Worker Route types
#


# PENDS python 3.9 support in pylint
# pylint: disable=inherit-non-class
# pylint: disable=too-few-public-methods
class Route(TypedDict):
    """Defines a Route for aio_pika.RPC.register."""
    path: str
    handler: WrappedRouteHandler


# PENDS python 3.9 support in pylint
# pylint: disable=inherit-non-class
# pylint: disable=too-few-public-methods
class Response(TypedDict):
    """Normalizes a successful response on a Route."""
    ok: bool
    data: str


RouteHandler = Callable[[NamedArg(str, 'data')], Awaitable[str]]
WrappedRouteHandler = Callable[[NamedArg(str, 'data')], Awaitable[Response]]


#
# Worker definition
#


class RPCWorker():
    """Simplify creating an RPC worker.

    Uses an overloaded version of aio-pika's RPC to add automatic
    JSON serialization/de-serialization & Gzip
    compression/decompression.

    See https://aio-pika.readthedocs.io/en/latest/patterns.html#rpc
    for more.
    """

    # properties
    _connection: Connection
    _channel: Channel
    _worker: RPC
    _connection_params: ConnectionParameters
    _exchange_name: str
    _routes: List[Route]
    logger: logging.Logger

    def __init__(
            self,
            connection_params: ConnectionParameters,
            exchange_name: str = os.getenv('BROKER_EXCHANGE_NAME', '')):
        self._connection_params = connection_params
        self._exchange_name = exchange_name
        self._routes = []
        self.logger = logging.getLogger(__name__)

    async def _start(self) -> None:
        """Starts the worker.

        Handles initializing a connection & creating a channel,
        then uses aio-pika's RPC.create to create a new worker,
        & finally registers every route created by the user.
        """
        print('starting...')
        self.logger.info('Starting RPC server...')

        host = self._connection_params.host
        port = self._connection_params.port

        self._connection = await connect_robust(
            host=host,
            port=port,
            login=self._connection_params.user,
            password=self._connection_params.password)
        self._channel = await self._connection.channel()
        self._worker = await CustomJsonGzipRPC.create(self._channel)

        async def register(route: Route) -> None:
            self.logger.info(
                f"Registering handler {route['handler'].__name__} on path {route['path']}")
            await self._worker.register(
                route['path'],
                # casting necessary because mypy gets a little confused about
                # expected type for RPC.register
                cast(Callable[[Any], Any], route['handler']))

        await asyncio.gather(*[register(route) for route in self._routes])

        self.logger.info(
            f'RPC worker waiting for tasks from {host}:{port}')

    async def _stop(self) -> None:
        """Defers to aio-pika.Connection's close method."""
        self.logger.info('RPC worker stopping...')
        # having mypy ignore the next line--calling close is necessary to
        # gracefully disconnect from rabbitmq broker, but aio_pika's
        # Connection.close method is untyped, throwing an "Call to untyped
        # function "close" in typed context" error when not ignored in strict
        # mode
        await self._connection.close()  # type: ignore

    def route(self, path: str) -> Callable[[RouteHandler], None]:
        """Decorator to add a new 'route' (queue & callback) to the worker.

        Similar to creating a route in Flask, this method
        listens on a given 'path' (queue) & executes the given
        handler (callback) when a message is received in that queue.
        """

        self.logger.debug(
            f'Begin processing route decorator with given path: {path}')

        def wrap_handler(
                path: str,
                handler: RouteHandler) -> WrappedRouteHandler:
            async def wrapped(*, data: str) -> Response:
                self.logger.info(f'TASK RECEIVED {path}')

                result = await handler(data=data)
                response = Response(ok=True, data=result)

                self.logger.info(
                    f'TASK COMPLETED {path}: {json.dumps(response)}')

                return response

            return wrapped

        def decorate_route(handler: RouteHandler) -> None:
            new_route = Route(
                path=path,
                handler=wrap_handler(path, handler))

            # FIXME: the problem might be here; these logs aren't showing
            # up so wrap_route doesn't appear to be getting called?
            self.logger.debug(
                f'Created new route: {new_route}')

            self._routes.append(new_route)

            self.logger.debug(
                f'Pushed new route to _routes: {self._routes}')

        return decorate_route

    async def run(self) -> Callable[[], Awaitable[None]]:
        """Start the RPC Worker.

        Must be called inside an asyncio event loop, such as
        `run_until_complete(run())`.
        """
        await self._start()

        return self._stop
