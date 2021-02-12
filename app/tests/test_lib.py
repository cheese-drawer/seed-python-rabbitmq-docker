import pytest

from src import lib


# NOTE: Using pytest-describe plugin to lend a more human readable syntax
# to organizing tests. This file shows a good way of simply but cleanly
# organizing unit tests for all methods contained in app/src/lib.py.
# Sometimes, a method might need multiple tests, so it is best to group
# each method's tests within a "Describe block"", using a test function
# that starts with `describe_`, as shown below. Then, within the "block",
# define each test for the method. Typically, you name the Describe block
# as `describe_{method_name}`.
def describe_do_a_quick_thing() -> None:

    def wont_return_an_int_less_than_0() -> None:
        assert lib.do_a_quick_thing() >= 0

    def wont_return_an_int_over_100() -> None:
        assert lib.do_a_quick_thing() <= 100


def describe_do_a_long_thing() -> None:

    # NOTE: This tests shows how to easily & cleanly test an asynchronous
    # function without having to worry about managing an event loop. This is
    # possible due to the dependency `pytest-asyncio`, a plugin that gives the
    # below @pytest.mark.asyncio decorator. This lets pytest know to run this
    # test function asynchronously.
    @pytest.mark.asyncio
    async def returns_string_that_took_forever() -> None:
        assert await lib.do_a_long_thing() == 'that took forever'
