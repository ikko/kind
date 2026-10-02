"""This module provides the scheduler: jobs that run a callable once or on a cron schedule.

A schedule file names functions by dotted path. Loading one imports and runs code, so a
Scheduler only resolves functions from modules it was explicitly allowed to use
(`allowed_modules`); everything else is refused. The clock is injectable (`now`), and
`run_due_jobs()` is one deterministic step of the loop that `start()` runs.
"""
import datetime
import heapq
import importlib
import inspect
import logging
import threading
import uuid
from typing import Any, Callable, Iterable, Optional, Union

import anyio
import anyio.abc
import anyio.to_thread
import orjson
from croniter import croniter

from kind.core.kind import Kind

log = logging.getLogger(__name__)

Schedule = Union[str, datetime.datetime, datetime.date, datetime.time, Kind]
Clock = Callable[[], datetime.datetime]


class CallableNotAllowedError(PermissionError):
    """Raised when a dotted path points outside the allowed modules."""


def resolve_callable(dotted_path: str, allowed_modules: Iterable[str]) -> Callable[..., Any]:
    """Imports `module.function` if the module is one of `allowed_modules` (or inside one)."""
    module_name, _, func_name = dotted_path.rpartition('.')
    allowed = tuple(allowed_modules)
    if not module_name or not any(module_name == a or module_name.startswith(f"{a}.") for a in allowed):
        raise CallableNotAllowedError(
            f"Refusing to import {dotted_path!r}: module {module_name or '?'!r} is not in allowed_modules "
            f"{list(allowed)}. Hint: pass allowed_modules=[{module_name!r}] (CLI: --allow-module "
            f"{module_name}) only if you trust the schedule file.")
    func = getattr(importlib.import_module(module_name), func_name)
    if not callable(func):
        raise TypeError(f"{dotted_path!r} is not callable")
    return func


def is_recurring(schedule: Schedule) -> bool:
    return isinstance(schedule, str) and croniter.is_valid(schedule)


class ScheduledJob:
    """A callable with its arguments and a schedule: cron string, ISO datetime, date, time or Kind."""

    def __init__(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None,
                 schedule: Optional[Schedule] = None, id: Optional[str] = None,
                 now: Optional[datetime.datetime] = None):
        if schedule is None:
            raise TypeError("ScheduledJob needs a schedule (cron string, ISO datetime, date, time or Kind).")
        self.id = id or str(uuid.uuid4())
        self.func = func
        self.args = tuple(args)
        self.kwargs = kwargs or {}
        self.schedule = schedule
        self.next_run: datetime.datetime
        self._calculate_next_run(now)

    def _calculate_next_run(self, base_time: Optional[datetime.datetime] = None) -> None:
        now = base_time or datetime.datetime.now()
        schedule = self.schedule
        if is_recurring(schedule):
            self.next_run = croniter(schedule, now).get_next(datetime.datetime)
        elif isinstance(schedule, (str, Kind)):
            text = schedule.name if isinstance(schedule, Kind) else schedule
            try:
                self.next_run = datetime.datetime.fromisoformat(text)
            except ValueError:
                raise ValueError(f"Schedule {text!r} is neither a cron expression nor an ISO 8601 datetime.") from None
        elif isinstance(schedule, datetime.datetime):
            self.next_run = schedule
        elif isinstance(schedule, datetime.date):
            self.next_run = datetime.datetime.combine(schedule, datetime.time.min)
        elif isinstance(schedule, datetime.time):
            self.next_run = datetime.datetime.combine(now.date(), schedule)
            if self.next_run < now:
                self.next_run += datetime.timedelta(days=1)
        else:
            raise TypeError(f"Unsupported schedule type: {type(schedule).__name__}")

    def __lt__(self, other: "ScheduledJob") -> bool:
        return self.next_run < other.next_run

    def to_dict(self) -> dict:
        """JSON-ready form: a recurring job keeps its cron string, a one-off job its next run."""
        return {
            "id": self.id,
            "func": f"{self.func.__module__}.{self.func.__qualname__}",
            "args": list(self.args),
            "kwargs": self.kwargs,
            "schedule": self.schedule if is_recurring(self.schedule) else self.next_run.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict, allowed_modules: Iterable[str] = (),
                  now: Optional[datetime.datetime] = None) -> "ScheduledJob":
        return cls(func=resolve_callable(data["func"], allowed_modules), args=tuple(data.get("args", ())),
                   kwargs=data.get("kwargs", {}), schedule=data["schedule"], id=data["id"], now=now)


class Scheduler:
    """A heap of jobs, run by `start()` in a task group or step by step with `run_due_jobs()`."""

    def __init__(self, schedule_file: Optional[str] = None, allowed_modules: Iterable[str] = (),
                 now: Clock = datetime.datetime.now):
        self._schedule: list[ScheduledJob] = []
        self._lock = threading.RLock()
        self._running = False
        self._now = now
        self.job_map: dict[str, ScheduledJob] = {}
        self.schedule_file = schedule_file
        self.allowed_modules = tuple(allowed_modules)
        if schedule_file:
            self.load_schedule()

    def add_job(self, job: ScheduledJob) -> None:
        self.add_jobs([job])

    def add_jobs(self, jobs: Iterable[ScheduledJob]) -> None:
        with self._lock:
            for job in jobs:
                heapq.heappush(self._schedule, job)
                self.job_map[job.id] = job
            self.save_schedule()

    def remove_job(self, job_id: str) -> Optional[ScheduledJob]:
        with self._lock:
            job = self.job_map.pop(job_id, None)
            if job:
                self._schedule.remove(job)
                heapq.heapify(self._schedule)
                self.save_schedule()
            return job

    def _pop_due(self, now: datetime.datetime) -> Optional[ScheduledJob]:
        with self._lock:
            if self._schedule and self._schedule[0].next_run <= now:
                return heapq.heappop(self._schedule)
            return None

    async def run_due_jobs(self) -> int:
        """Runs every job due now (outside the lock), reschedules recurring ones; returns the count."""
        now, ran = self._now(), 0
        while (job := self._pop_due(now)) is not None:
            log.info(f"Running job {job.id}")
            if inspect.iscoroutinefunction(job.func):
                await job.func(*job.args, **job.kwargs)
            else:
                await anyio.to_thread.run_sync(lambda: job.func(*job.args, **job.kwargs))
            ran += 1
            with self._lock:
                if is_recurring(job.schedule) and job.id in self.job_map:
                    job._calculate_next_run(base_time=now)
                    heapq.heappush(self._schedule, job)
                else:
                    self.job_map.pop(job.id, None)
                self.save_schedule()
        return ran

    def seconds_until_next_job(self, default: float = 1.0) -> float:
        with self._lock:
            if not self._schedule:
                return default
            return max(0.0, (self._schedule[0].next_run - self._now()).total_seconds())

    async def _run(self) -> None:
        while self._running:
            await self.run_due_jobs()
            await anyio.sleep(max(0.01, min(self.seconds_until_next_job(), 1.0)))

    async def start(self, task_group: anyio.abc.TaskGroup) -> None:
        if not self._running:
            self._running = True
            task_group.start_soon(self._run)

    async def stop(self) -> None:
        self._running = False

    def save_schedule(self) -> None:
        if not self.schedule_file:
            return
        with self._lock, open(self.schedule_file, "wb") as f:
            f.write(orjson.dumps([job.to_dict() for job in self.job_map.values()]))

    def load_schedule(self) -> None:
        """Loads jobs from the schedule file; functions must come from allowed_modules."""
        if not self.schedule_file:
            return
        try:
            with open(self.schedule_file, "rb") as f:
                jobs_data = orjson.loads(f.read())
        except FileNotFoundError:
            return
        jobs = [ScheduledJob.from_dict(data, self.allowed_modules, now=self._now()) for data in jobs_data]
        with self._lock:
            for job in jobs:
                heapq.heappush(self._schedule, job)
                self.job_map[job.id] = job
