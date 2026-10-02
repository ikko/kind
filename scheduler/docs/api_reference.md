## `kind_scheduler.batch` Module


> ⚠ _This package is under development. Where this page and the code differ, the code is right; test your schedules, especially the async batch functions._
 

This module provides functions for processing batches of items concurrently: sync functions run in worker threads, async functions run as tasks. Results keep the order of the input.



### Function: `a_process_batch`
<!-- doc-example: not-run — a signature, not a program -->
```python
async def a_process_batch(batch: Iterable[T], func: Callable[[T], Union[U, Awaitable[U]]]) -> List[U]
```

*   **Description**: Asynchronously processes a batch of items using the given function, all items concurrently.
*   **Parameters**:
    *   `batch` (`Iterable[T]`): An iterable of items to process.
    *   `func` (`Callable[[T], Union[U, Awaitable[U]]]`): An async or sync function to apply to each item. Sync functions run in worker threads.
*   **Returns**: `List[U]` - The results, in the order of the input.

### Function: `process_batch`
<!-- doc-example: not-run — a signature, not a program -->
```python
def process_batch(batch: Iterable[T], func: Callable[[T], U], new_thread: bool = True) -> List[U]
```

*   **Description**: Synchronously processes a batch of items using the given function.
*   **Parameters**:
    *   `batch` (`Iterable[T]`): An iterable of items to process.
    *   `func` (`Callable[[T], U]`): A sync function to apply to each item.
    *   `new_thread` (`bool`): If `True` (default), items are processed concurrently in worker threads (via `a_process_batch`); if `False`, in order in the calling thread.
*   **Returns**: `List[U]` - The results, in the order of the input.

---

## `kind_scheduler.schedule` Module

This module provides the core scheduling logic of `kind-scheduler`. A schedule file names functions by dotted path; loading one imports and runs code, so a `Scheduler` only resolves functions from the modules it was explicitly allowed to use (`allowed_modules`). Anything else raises `CallableNotAllowedError`.

### Class: `ScheduledJob`
* **Description**: Represents a single scheduled job.
* **Constructor**: `ScheduledJob()`
<!-- doc-example: not-run — a signature, not a program -->
```python
def __init__(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None, schedule: Optional[Union[str, datetime.datetime, datetime.date, datetime.time, Kind]] = None, id: Optional[str] = None, now: Optional[datetime.datetime] = None)
```

* **Description**: Initializes a new `ScheduledJob`.
* **Parameters**:
    *   `func`: The function to execute (sync functions run in a worker thread, async functions are awaited).
    *   `args`: Positional arguments for the function.
    *   `kwargs`: Keyword arguments for the function.
    *   `schedule`: The schedule for the job. Can be a cron string, an ISO 8601 datetime string, a `datetime.datetime` object, a `datetime.date` object, a `datetime.time` object, or a `Kind` with a name that can be parsed as an ISO 8601 datetime string. Required: omitting it raises `TypeError`.
    *   `id`: An optional ID for the job (a UUID by default).
    *   `now`: The base time for computing the first run (defaults to the current time).

### Class: `Scheduler`
* **Description**: Manages the schedule of jobs.
* **Constructor**: `Scheduler()`  
<!-- doc-example: not-run — a signature, not a program -->
```python
def __init__(self, schedule_file: Optional[str] = None, allowed_modules: Iterable[str] = (), now: Callable[[], datetime.datetime] = datetime.datetime.now)
```

*   **Description**: Initializes a new `Scheduler`.
*   **Parameters**:
    *   `schedule_file`: An optional file path to save and load the schedule.
    *   `allowed_modules`: The modules (and their submodules) whose functions a schedule file may name.
    *   `now`: The clock; inject one to make scheduling deterministic.
* **`add_job(self, job: ScheduledJob)`** / **`add_jobs(self, jobs: Iterable[ScheduledJob])`**
    *   **Description**: Adds jobs to the schedule.
* **`remove_job(self, job_id: str) -> Optional[ScheduledJob]`**
    *   **Description**: Removes a job from the schedule by its ID.
* **`async run_due_jobs(self) -> int`**
    *   **Description**: Runs every job that is due now, reschedules recurring ones and returns how many ran: one deterministic step of the scheduler loop.
* **`async start(self, task_group: anyio.abc.TaskGroup)`**
    *   **Description**: Starts the scheduler loop as a task in the given task group.
* **`async stop(self)`**
    *   **Description**: Stops the scheduler.
* **`save_schedule(self)`**
    *   **Description**: Saves the current schedule to the schedule file.
* **`load_schedule(self)`**
    *   **Description**: Loads the schedule from the schedule file; functions must come from `allowed_modules`.

---

## `kind_scheduler.cli` Module

The `kind-scheduler` console script (Typer) over a schedule file: `kind-scheduler -f FILE -m MODULE add|list|remove|run`. `-m`/`--allow-module` (repeatable) names the modules whose functions jobs may run.
