import anyio
import pytest

from kind_scheduler.batch import a_process_batch, process_batch


def square(x):
    return x * x


async def async_square(x):
    await anyio.sleep(0.01 * (5 - x))  # later items finish first ...
    return x * x


@pytest.mark.parametrize("new_thread", [False, True])
def test_process_batch_keeps_input_order(new_thread):
    assert process_batch([1, 2, 3], square, new_thread=new_thread) == [1, 4, 9]


@pytest.mark.anyio
async def test_a_process_batch_async_results_follow_input_order():
    assert await a_process_batch([1, 2, 3, 4], async_square) == [1, 4, 9, 16]  # ... results still in input order


@pytest.mark.anyio
async def test_a_process_batch_sync_function_in_threads():
    assert await a_process_batch(range(5), square) == [0, 1, 4, 9, 16]


def test_empty_batch():
    assert process_batch([], square) == []
