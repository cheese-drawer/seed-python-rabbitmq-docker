"""
Classes for making working with RabbitMQ RPC workers easier.

Powered by aio-pika.
"""

from __future__ import annotations
import asyncio
import inspect
import json
from typing import (cast,
                    Any,
                    Awaitable,
                    Callable,
                    List,
                    TypedDict)

from aio_pika.patterns import RPC
from mypy_extensions import NamedArg

from connection import connect, ConnectionParameters
from response import Response, OkResponse, ErrResponse
from serializer import serialize, deserialize
from worker_base import Worker

#
# EXTENDING aio_pika.RPC
#


class CustomJSONGzipRPC(RPC):
    """Extend RPC pattern from aio-pika.

    - Automates encoding as JSON & UTF8, then compresses messages with Gzip.
    - Specifies what type of data must be given in order to be serialized
    """

    SERIALIZER = json
    CONTENT_TYPE = 'application/octet-stream'

    def serialize(self, data: Response) -> bytes:
        """Serialize the data being sent in the message.

        Arguments:
        - data: Response -- The data to be serialized

        Returns:
        - bytes

        Defers to shared serialize function to handle serialization
        using the SERIALIZER specified as a class constant.
        """
        return serialize(self.SERIALIZER, data)

    def serialize_exception(self, exception: Exception) -> bytes:
        """Wrap exceptions thrown by aio_pika.RPC in an ErrResponse."""
        return self.serialize(ErrResponse(exception))

    def deserialize(self, data: bytes) -> bytes:
        """Decompress incoming message, then defer to aio_pika.RPC."""
        # Example at https://aio-pika.readthedocs.io/en/latest/patterns.html
        # doesn't bother with decoding from bytes to string or
        # decoding json; apparently builtin `pickle` dependency
        # handles all of that on it's own.
        return super().deserialize(deserialize(data))


#
# WORKER ROUTE TYPES
#


RouteHandler = Callable[[NamedArg(str, 'data')], Awaitable[Any]]


class Route(TypedDict):
    """Defines a Route for aio_pika.RPC.register."""

    # PENDS python 3.9 support in pylint
    # pylint: disable=inherit-non-class
    # pylint: disable=too-few-public-methods

    path: str
    handler: RouteHandler


#
# Worker definition
#


class RPCWorker(Worker):
    """Simplify creating an RPC worker.

    Uses an overloaded version of aio-pika's RPC to add automatic
    JSON serialization/de-serialization & Gzip
    compression/decompression.

    See https://aio-pika.readthedocs.io/en/latest/patterns.html#rpc
    for more.
    """

    # property types
    _worker: RPC
    _routes: List[Route]

    # class constants
    PATTERN = CustomJSONGzipRPC

    def __init__(
            self,
            connection_params: ConnectionParameters,
            name: str = 'RPCWorker'):
        self._routes = []
        self.worker_name = name
        super().__init__(connection_params)

    async def _start(self) -> None:
        """Start the worker.

        Handles initializing a connection & creating a channel,
        then uses aio-pika's RPC.create to create a new worker,
        & finally registers every route created by the user.
        """
        self.logger.info('Starting RPC worker...')

        host, port, self._connection, self._channel = await connect(
            self._connection_params)
        # pylint doesn't seem to understand that PATTERN here is
        # a class variable & still accessible through `self`
        # pylint: disable=no-member
        self._worker = await self.PATTERN.create(self._channel)

        async def register(route: Route) -> None:
            self.logger.info(
                f"Registering handler {route['handler'].__name__} "
                f"on path {route['path']}")
            await self._worker.register(
                route['path'],
                # casting necessary because mypy gets a little confused about
                # expected type for RPC.register
                cast(Callable[[Any], Any], route['handler']))

        await asyncio.gather(*[register(route) for route in self._routes])

        self.logger.info(
            f'Worker waiting for tasks from {host}:{port}')

    def route(self, path: str) -> Callable[[RouteHandler], None]:
        """Add new 'route' (consumer queue) to the worker with this Decorator.

        Similar to creating a route in Flask, this method listens on a given
        'path' (queue name) & executes the given handler (callback) when a
        message is received in that queue.
        """
        self.logger.debug(
            f'Begin processing route decorator with given path: {path}')

        def wrap_handler(
                path: str,
                handler: RouteHandler) -> RouteHandler:
            async def wrapped(*, data: str) -> Response:
                self.logger.info(f'TASK RECEIVED {path}')

                response: Response

                try:
                    result = await handler(data=data)
                    response = OkResponse(result)
                # Ignoring broad-except pylint warning here because the intent
                # is to catch every error thrown while awaiting & executing a
                # handler; this allows it to be wrapped in an ErrResponse &
                # communicated clearly to the original Requester
                except Exception as err:  # pylint: disable=broad-except
                    response = ErrResponse(err)

                self.logger.info(
                    f'TASK COMPLETED {path}: {repr(response)}')

                return response

            return wrapped

        def decorate_route(handler: RouteHandler) -> None:
            if inspect.iscoroutinefunction(handler):
                new_route = Route(
                    path=path,
                    handler=wrap_handler(path, handler))

                self.logger.debug(
                    f'Created new route: {new_route}')

                self._routes.append(new_route)

                self.logger.debug(
                    f'Pushed new route to _routes: {self._routes}')
            else:
                raise TypeError(
                    f'Handler {handler} must be a coroutine function')

        return decorate_route
