import server
from start_server import run

# Run all registered workers
# NOTE: using run like this encapsulates all the asyncio event loop
# management to run all of the workers passed to `register_worker()`
# simultaneously & asynchronously without having to clutter up the code
# here for the application API
run()
