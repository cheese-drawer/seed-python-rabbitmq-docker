"""Encapsulates logic used to actually run the application.

Provided as an abstraction to avoid errors in configuration
while defining application logic in main.py.
"""

import asyncio
from typing import Any, Protocol, Awaitable, Callable, List

# PENDS python 3.9 support in pylint
# pylint: disable=too-few-public-methods


class Runnable(Protocol):
    """Protocol specifying that a 'runnable' object.

    Requires object to have a `run` method that returns an async function
    that resolves to none when called.
    """

    def run(self) -> Awaitable[Callable[[], Awaitable[None]]]:
        """Run the object implementing a Runnable protocol."""
        ...


workers: List[Runnable] = []


def register_worker(worker: Runnable) -> None:
    """Add worker to list to be run when application is run.

    Executes worker in asyncio event loop. Allows multiple workers
    by taking all workers registered via this method, then using
    asyncio.gather to execute all in parallel.
    """
    workers.append(worker)


async def _run_workers() -> Any:
    """Gather all registered workers & await them to execute in event loop."""
    return await asyncio.gather(*[worker.run() for worker in workers])


async def _stop_workers(
    stop_methods: List[Callable[[], Awaitable[None]]]
) -> Any:
    """Collect worker _stop methods & await them, similar to _run_workers."""
    return await asyncio.gather(*[stop() for stop in stop_methods])


def run() -> None:
    """Run all registered workers in asyncio loop.

    Gracefully exit using CTRL-C.
    """
    # setup an event loop w/ asyncio
    loop = asyncio.get_event_loop()
    # tell it to start the worker & assign the result to variable
    # to be used later to stop the worker
    stop_methods = loop.run_until_complete(_run_workers())

    try:
        # enter an infinite loop to wait for tasks
        loop.run_forever()
    except KeyboardInterrupt:
        # but setup graceful exit on KeyboardInterrupt
        pass
    finally:
        # by allowing worker to stop completely before killing process
        loop.run_until_complete(_stop_workers(stop_methods))

    loop.close()
