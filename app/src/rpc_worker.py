"""
Classes for making working with RabbitMQ RPC workers easier.

Powered by aio-pika.
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass
import inspect
import gzip
import json
import logging
import os
import traceback
from typing import (cast,
                    Literal,
                    Any,
                    Union,
                    Awaitable,
                    Callable,
                    List,
                    Tuple,
                    TypedDict,
                    Dict)

from aio_pika.patterns import RPC
from aio_pika.channel import Channel
from aio_pika.connection import Connection
from aio_pika import connect_robust
from dotenv import load_dotenv
from mypy_extensions import NamedArg


load_dotenv(os.path.abspath('app/.secrets'))

#
# RESPONSE TYPES
#


class Response:
    """Normalizes a successful response on a Route."""

    # class is essentially a @dataclass, but needs ABC inheritance to work
    # correctly for mypy, ignoring pylint error about number of methods
    # pylint: disable=too-few-public-methods

    success: bool

    def __init__(self, success: bool) -> None:
        self.success = success


# PENDS python 3.9 support in pylint
# pylint: disable=unsubscriptable-object
OkResponseData = Union[str,
                       Dict[str, Any],
                       List[Any],
                       Tuple[Any],
                       int,
                       float,
                       bool]


class OkResponse(Response):
    """Response type to communicate a successful reply to the Request."""

    # class is essentially a @dataclass, but needs ABC inheritance to work
    # correctly for mypy, ignoring pylint error about number of methods
    # pylint: disable=too-few-public-methods

    # PENDS python 3.9 typing support in pylint
    # pylint: disable=unsubscriptable-object
    success: Literal[True]
    data: OkResponseData

    def __init__(self, data: OkResponseData) -> None:
        super().__init__(True)
        self.data = data


class ErrResponse(Response):
    """Response type to communicate an error with processing the Request."""

    # class is essentially a @dataclass, but needs ABC inheritance to work
    # correctly for mypy, ignoring pylint error about number of methods
    # pylint: disable=too-few-public-methods

    ErrorData = TypedDict('ErrorData', {
        'type': str,
        'message': str,
        'args': Tuple[Any, ...],
        'trace': str,
    })

    # PENDS python 3.9 typing support in pylint
    success: Literal[False]  # pylint: disable=unsubscriptable-object
    error: ErrorData

    def __init__(self, error: Exception) -> None:
        super().__init__(False)
        self.error = {
            'type': error.__class__.__name__,
            'message': repr(error),
            'args': error.args,
            'trace': ''.join(
                traceback.format_exception(
                    etype=type(error),
                    value=error,
                    tb=error.__traceback__)),
        }


#
# EXTENDING aio_pika.RPC
#


DEFAULT_EXCHANGE_NAME = os.getenv('BROKER_EXCHANGE_NAME', RPC.DLX_NAME)
print(f'default exchange name: {DEFAULT_EXCHANGE_NAME}')


class CustomJSONGzipRPC(RPC):
    """Extend RPC pattern from aio-pika.

    - Automates encoding as JSON & UTF8, then compresses messages with Gzip.
    - Specifies what type of data must be given in order to be serialized
    """

    # override default exchange name in aio_pika.patterns.rpc.RPC
    # has to be done via environment variable to avoid complex
    # changes to RPC's __init__ or create methods
    DLX_NAME = DEFAULT_EXCHANGE_NAME

    SERIALIZER = json
    CONTENT_TYPE = 'application/octet-stream'

    def serialize(self, data: Response) -> bytes:
        """Serialize the data being sent in the message.

        Arguments:
        - data: Response -- The data to be serialized

        Returns:
        - bytes

        The provided data must be json serializable. This method will attempt
        to serialize it by using first converting it to a dictionary using
        `vars()`, then using the string returned by calling `repr()` on it.
        If neither of those works, then a TypeError will be raised.
        """
        try:
            as_json = self.SERIALIZER.dumps(
                data,
                ensure_ascii=False,
            )
        except TypeError as err:
            err_msg = err.args[0]
            if 'not JSON serializable' in err_msg:
                try:
                    as_json = self.SERIALIZER.dumps(
                        vars(data),
                        ensure_ascii=False,
                        default=repr,
                    )
                except TypeError:
                    raise TypeError(
                        'The Route\'s response is not JSON serializable'
                    ) from err

        return gzip.compress(as_json.encode('UTF8'))

    def serialize_exception(self, exception: Exception) -> bytes:
        """Wrap exceptions thrown by aio_pika.RPC in an ErrResponse."""
        return self.serialize(ErrResponse(exception))

    def deserialize(self, data: Any) -> bytes:
        """Decompress incoming message, then defer to aio_pika.RPC."""
        # Example at https://aio-pika.readthedocs.io/en/latest/patterns.html
        # doesn't bother with decoding from bytes to string or
        # decoding json; apparently builtin `pickle` dependency
        # handles all of that on it's own.
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
        """Start the worker.

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
        self._worker = await CustomJSONGzipRPC.create(self._channel)

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

    async def run(self) -> Callable[[], Awaitable[None]]:
        """Start the RPC Worker.

        Must be called inside an asyncio event loop, such as
        `run_until_complete(run())`.
        """
        await self._start()

        return self._stop
