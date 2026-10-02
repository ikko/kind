# Use Kinds from threads and async code

Mutations of one space are serialized by its `RLock` (`space.lock`); reads of children, parents and relations iterate snapshots copied under that lock; composite operations made of several calls are not atomic as a whole. Which space `Kind(name)` uses is decided by a context variable, so it follows the context, not the thread.

## Which space a task sees

| runs in | current space |
|---|---|
| asyncio / trio task | inherited from the code that created the task |
| `anyio.to_thread.run_sync` worker | inherited (anyio copies the context) |
| `threading.Thread(target=f)` | the **default** space |
| `threading.Thread(target=contextvars.copy_context().run, args=(f,))` | inherited |
| `concurrent.futures.ThreadPoolExecutor` worker | the default space, unless you submit `copy_context().run` |
| `asyncio.to_thread` | inherited |

```python
import asyncio
import contextvars
import threading

import anyio
import anyio.to_thread
from kind import KindSpace, current_space

seen = {}
with KindSpace(name='job'):
    plain = threading.Thread(target=lambda: seen.__setitem__('Thread', current_space().name))
    plain.start(); plain.join()

    context = contextvars.copy_context()
    copied = threading.Thread(target=context.run,
                              args=(lambda: seen.__setitem__('Thread + copy_context', current_space().name),))
    copied.start(); copied.join()

    async def worker_thread():
        return await anyio.to_thread.run_sync(lambda: current_space().name)
    seen['anyio.to_thread'] = anyio.run(worker_thread)

    async def task():
        return await asyncio.create_task(asyncio.sleep(0, result=current_space().name))
    seen['asyncio task'] = asyncio.run(task())

for runner, space in seen.items():
    print(f"{runner}: {space}")
```
<details>
<summary>Outcome</summary>

```text
Thread: default
Thread + copy_context: job
anyio.to_thread: job
asyncio task: job
```
</details>

A plain thread that creates Kinds while you expected a private space writes into the default space instead. Start threads with `copy_context().run`, or enter the space inside the thread's target.

## What the lock covers

Each call that changes a Kind (`append`, `insert`, `relate`, `unrelate`, `delete`, `reparent`, creating a Kind, `Kind.next()`) holds the lock of the Kind's space for its whole duration, and checks every Kind it will change before changing any, so a refusal (frozen Kind, closed space) never leaves a half-applied edit. `patch` checks first and then performs one `append`/`relate` per edge, each under the lock, so as a whole it is a composite operation. Traversals, rendering and serialization copy each Kind's children, parents and relations under the lock and then iterate the copies, so a concurrent writer cannot break an iteration; a long traversal may still see some Kinds before and others after a concurrent change.

```python
import contextvars
import threading
from kind import Kind, KindSpace

with KindSpace(name='load'):
    root = Kind('Root')

    def add_children(worker):
        for i in range(1000):
            root.append(Kind(f"w{worker}_{i}"))

    threads = [threading.Thread(target=contextvars.copy_context().run, args=(add_children, w)) for w in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print(len(root.children), Kind.len())
```
<details>
<summary>Outcome</summary>

```text
4000 4001
```
</details>

## Composite operations

"Look, then change" spans two calls, and another thread can change the graph in between. Hold the space's lock around the whole sequence; it is reentrant, so the calls inside take it again without blocking.

```python
from kind import Kind, KindSpace

with KindSpace(name='orders'):
    queue = Kind('Queue')

    def enqueue_once(name):
        with queue.space.lock:          # check and append as one step
            if Kind(name) not in queue.children:
                queue.append(Kind(name))

    enqueue_once('order-1')
    enqueue_once('order-1')
    print([child.name for child in queue.children])
```
<details>
<summary>Outcome</summary>

```text
['order-1']
```
</details>

Different spaces have different locks, so work in separate spaces does not contend. The mixin registry is process-wide and is not guarded by any space lock: register mixins at start-up, then call `lock_mixins()` (see [write a mixin](write_a_mixin.md)).
