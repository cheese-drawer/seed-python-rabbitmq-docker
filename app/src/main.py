"""A simple example of implementing an API via AMQP via an RPC pattern.

Uses custom wrapping of aio_pika (which is itself a wrapper on aiomrq)
to simplify interacting with AMQP to the point of barely needing to
interact with it.

Uses a declarative API based on decorators, similar to Flask to declare API
'routes'.  These routes are really callback functions assigned to a queue
(named in the decorator argument) that executes any time a message (given
as the data keyword argument to the callback) is received on that queue.
The return value of the handler is then sent as the response directly to the
message originator.

The RPC worker runs asynchronously, allowing it to handle multiple requests
simultaneously & not block on a particularly long-running handler.
This requires running the worker in an asynchronous event loop, handled here
by the `register_worker` & `run` methods from `start_server`.
"""

# stdlib imports
import asyncio
import logging
import os

# external dependencies
from dotenv import load_dotenv

# internal dependencies
from rpc_worker import RPCWorker, ConnectionParameters
from start_server import register_worker, run

#
# ENVIRONMENT
#

# Loads environment variables stored in a secrets dotfile keep sensitive
# information here (i.e. broker authentication data, host address, etc.)
# to avoid having it committed in git This file requires manual creation,
# see README for more information.
load_dotenv(os.path.abspath('app/.secrets'))


def get_mode() -> str:
    """Helper to determine if running as 'production' or 'development'.

    Uses `MODE` environment variable & falls back to 'development' if no
    variable exists. Requires mode to be set to either 'development' OR
    'production', raises an error if anything else is specified.
    """

    env = os.getenv('MODE', 'development')  # default to 'development'

    if env in ('development', 'production'):
        return env

    raise TypeError(
        'MODE must be either [production], [development], or unset (defaults to [development])')


MODE = get_mode()


#
# LOGGING
#

LOGGER = logging.getLogger(__name__)
# NOTE: use this one for debugging, very verbose output
# logging.basicConfig(level=logging.DEBUG)
# NOTE: or use this one for production or development
# sets development logging based on MODE
logging.basicConfig(level=logging.INFO
                    if MODE == 'development'
                    else logging.ERROR)


#
# WORKER SETUP
#

# get connection parameters from dotenv, or use defaults
connection_params = ConnectionParameters(
    host=os.getenv('BROKER_HOST', 'localhost'),
    port=int(os.getenv('BROKER_PORT', '5672')),
    user=os.getenv('BROKER_USER', 'guest'),
    password=os.getenv('BROKER_PASS', 'guest'))

# initialize Worker & assign to global variable
rpc = RPCWorker(connection_params)


#
# WORKER ROUTES
#

# NOTE: use route decorator on RPCWorker instance similar to defining a
# route in Flask
# but this supports async route handlers, recommended for any task
# that you think might take a while (or just use all the time)

# NOTE: This is the section that you'll change the most; it's possible that
# you won't need to change anything else in many scenarios (I think)


# NOTE: define a route using the @rpc.route decorator provided by RPCWorker
# name the route as a string argument provided to the decorator then
# define a function immediately after the decorator that will handle all
# messages received on the named route
@rpc.route('test')
# NOTE: routes must return a string, this will be the message sent via the worker
# most of the time, you'll probably use `json.dumps` to encode your data as a string
# but sometimes it may not get all the attributes you want, so I didn't make
# the route decorator automatically encode it for you
async def test(*, data: str) -> str:
    """This is just a contrived example of an long running handler
    that uses async/await to allow other tasks to be handled while
    this one runs.
    """
    result = f'{data} processed'
    await asyncio.sleep(1)  # pretend to do work that takes 1 second
    LOGGER.info(result)  # print result when processed
    # tasks must return an object capable of being JSON serialized
    # the result is sent as JSON reply to the task originator
    return result


#
# NOTE: Documenting a possible common mistake
#
# - uncomment to see what it looks like in the type checker
# - delete in production
#
# @rpc.route('sync_test')
# def sync_test(*, data: str) -> str:
#     """This is an example of an easy mistake to make if not using mypy type checking.
#
#     `rpc.route` decorator can only be used on async functions. Type checking will
#     alert you if you forget the async keyword, but if you run the code (either because
#     you missed the mypy error or aren't using type checking) then the error will be
#     rather cryptic, like the following:
#
#         Exception: TypeError("object str can't be used in 'await' expression")
#     """
#     result = f'{data} processed synchronously'
#     LOGGER.info(result)
#
#     return result


#
# RUN WORKER
#

# adds rpc to list of workers to be run when application is executed
# run application by calling `python -m app/src` from project root
register_worker(rpc)

# run all registered workers
run()