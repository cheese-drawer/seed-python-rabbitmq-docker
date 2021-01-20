"""Encapsulates logic used to actually run the application.

Provided as an abstraction to avoid errors in configuration
while defining application logic in main.py.
"""

import asyncio
from typing import Any, Protocol, Awaitable, Callable, List

# PENDS python 3.9 support in pylint
# pylint: disable=too-few-public-methods


class Runnable(Protocol):
    """Protocol specifying that a class has a `run` method that
    returns an async function that resolves to none when called."""

    def run(self) -> Awaitable[Callable[[], Awaitable[None]]]:
        """Method to run the class implementing a Runnable protocol."""
        ...


workers: List[Runnable] = []


def register_worker(worker: Runnable) -> None:
    """Adds worker to list to be run when application is run.

    Executes worker in asyncio event loop. Allows multiple workers
    by taking all workers registered via this method, then using
    asyncio.gather to execute all in parallel.
    """
    workers.append(worker)


async def _run_workers() -> Any:
    """Gathers all workers defined in main & awaits them,
    ready to be run in event loop.
    """
    return await asyncio.gather(*[worker.run() for worker in workers])


def run() -> None:
    """Run all registered workers in asyncio loop.

    Gracefully exit using CTRL-C.
    """
    # setup an event loop w/ asyncio
    loop = asyncio.get_event_loop()
    # tell it to start the worker & assign the result to variable
    # to be used later to stop the worker
    stop_worker = loop.run_until_complete(_run_workers())

    try:
        # enter an infinite loop to wait for tasks
        loop.run_forever()
    except KeyboardInterrupt:
        # but setup graceful exit on KeyboardInterrupt
        pass
    finally:
        # by allowing worker to stop completely before killing process
        loop.run_until_complete(stop_worker())

    loop.close()
