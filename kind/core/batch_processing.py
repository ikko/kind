"""This module applies a function to every item of a batch, concurrently.

Sync functions run in worker threads; async functions run as tasks. Results keep the
order of the input.
"""
import inspect
from typing import Awaitable, Callable, Iterable, List, TypeVar, Union

import anyio
import anyio.to_thread

T = TypeVar('T')
U = TypeVar('U')


async def a_process_batch(batch: Iterable[T], func: Callable[[T], Union[U, Awaitable[U]]]) -> List[U]:
    """Runs `func` on every item concurrently and returns the results in input order."""
    items = list(batch)
    results: List[U] = [None] * len(items)  # type: ignore[list-item]

    async def run_one(position: int, item: T) -> None:
        if inspect.iscoroutinefunction(func):
            results[position] = await func(item)
        else:
            sync_func: Callable[[T], U] = func  # type: ignore[assignment]  # not a coroutine function here
            results[position] = await anyio.to_thread.run_sync(sync_func, item)

    async with anyio.create_task_group() as task_group:
        for position, item in enumerate(items):
            task_group.start_soon(run_one, position, item)
    return results


def process_batch(batch: Iterable[T], func: Callable[[T], U], new_thread: bool = True) -> List[U]:
    """Synchronous entry point: concurrent in threads (default), or in order in this thread."""
    if not new_thread:
        return [func(item) for item in batch]
    return anyio.run(a_process_batch, batch, func)
