"""Scheduler: job construction, deterministic stepping on a fake clock, persistence, the allowlist, the CLI."""
import datetime

import anyio
import orjson
import pytest
from typer.testing import CliRunner

from kind_scheduler.cli import app
from kind.core.kind import Kind
from kind_scheduler.schedule import CallableNotAllowedError, ScheduledJob, Scheduler, resolve_callable

THIS_MODULE = __name__
RESULTS: list = []


def sync_job(tag="sync"):
    RESULTS.append(tag)


async def async_job(tag="async"):
    await anyio.sleep(0)
    RESULTS.append(tag)


class FakeClock:
    def __init__(self, start: datetime.datetime):
        self.now = start

    def __call__(self) -> datetime.datetime:
        return self.now

    def advance(self, **delta) -> None:
        self.now += datetime.timedelta(**delta)


@pytest.fixture(autouse=True)
def clear_results():
    RESULTS.clear()


@pytest.fixture
def clock():
    return FakeClock(datetime.datetime(2026, 10, 2, 12, 0, 0))


# --- ScheduledJob ------------------------------------------------------------

@pytest.mark.parametrize("schedule, expected", [
    (datetime.datetime(2026, 1, 1, 8, 0), datetime.datetime(2026, 1, 1, 8, 0)),
    (datetime.date(2026, 1, 1), datetime.datetime(2026, 1, 1, 0, 0)),
    ("2025-12-25T10:00:00", datetime.datetime(2025, 12, 25, 10, 0)),
    (Kind("2025-01-01T00:00:00"), datetime.datetime(2025, 1, 1, 0, 0)),
    (datetime.time(13, 0), datetime.datetime(2026, 10, 2, 13, 0)),   # later today
    (datetime.time(11, 0), datetime.datetime(2026, 10, 3, 11, 0)),   # already passed: tomorrow
    ("*/5 * * * *", datetime.datetime(2026, 10, 2, 12, 5)),
])
def test_next_run(schedule, expected, clock):
    assert ScheduledJob(sync_job, schedule=schedule, now=clock()).next_run == expected


def test_past_datetime_is_kept_and_runs_immediately(clock):
    past = clock() - datetime.timedelta(days=1)
    assert ScheduledJob(sync_job, schedule=past, now=clock()).next_run == past


@pytest.mark.parametrize("schedule, error", [(123, TypeError), ("not a schedule", ValueError), (None, TypeError)])
def test_invalid_schedule(schedule, error):
    with pytest.raises(error):
        ScheduledJob(sync_job, schedule=schedule)


def test_jobs_order_by_next_run(clock):
    soon, later = (ScheduledJob(sync_job, schedule=clock() + datetime.timedelta(seconds=s)) for s in (5, 10))
    assert soon < later and not later < soon


@pytest.mark.parametrize("schedule", ["*/5 * * * *", datetime.datetime(2026, 1, 1, 8, 0), datetime.time(13, 0)])
def test_dict_round_trip(schedule, clock):
    job = ScheduledJob(sync_job, (1, "x"), {"tag": "v"}, schedule, id="job-1", now=clock())
    data = orjson.loads(orjson.dumps(job.to_dict()))  # what a schedule file holds
    again = ScheduledJob.from_dict(data, allowed_modules=[THIS_MODULE])
    assert (again.id, again.func, again.args, again.kwargs) == ("job-1", sync_job, (1, "x"), {"tag": "v"})
    if isinstance(schedule, str):
        assert again.schedule == schedule  # recurring jobs keep their cron expression
    else:
        assert again.next_run == job.next_run


# --- the allowlist --------------------------------------------------------------

@pytest.mark.parametrize("dotted, allowed", [
    ("os.system", []),
    ("os.system", ["tests"]),
    ("subprocess.run", [THIS_MODULE]),
    ("system", [THIS_MODULE]),
    ("testsx.core.f", ["tests"]),  # a prefix must end at a dot
])
def test_resolve_callable_refuses_modules_outside_the_allowlist(dotted, allowed):
    with pytest.raises(CallableNotAllowedError, match="allowed_modules"):
        resolve_callable(dotted, allowed)


def test_resolve_callable_accepts_allowed_modules_and_their_submodules():
    from kind.core.kind import to_kind
    assert resolve_callable(f"{THIS_MODULE}.sync_job", [THIS_MODULE]) is sync_job
    assert resolve_callable("kind.core.kind.to_kind", ["kind"]) is to_kind


def test_loading_a_malicious_schedule_file_runs_nothing(tmp_path):
    evil = tmp_path / "evil.json"
    evil.write_bytes(orjson.dumps([{"id": "x", "func": "os.system", "args": ["touch pwned"],
                                    "kwargs": {}, "schedule": "* * * * *"}]))
    with pytest.raises(CallableNotAllowedError):
        Scheduler(schedule_file=str(evil))
    assert not (tmp_path / "pwned").exists()


# --- stepping on a fake clock ------------------------------------------------

@pytest.mark.anyio
async def test_one_off_jobs_run_once_when_due(clock):
    scheduler = Scheduler(now=clock)
    scheduler.add_jobs([ScheduledJob(sync_job, ("s",), schedule=clock() + datetime.timedelta(seconds=10)),
                        ScheduledJob(async_job, ("a",), schedule=clock() + datetime.timedelta(seconds=20))])
    assert await scheduler.run_due_jobs() == 0
    clock.advance(seconds=10)
    assert await scheduler.run_due_jobs() == 1 and RESULTS == ["s"]
    clock.advance(seconds=10)
    assert await scheduler.run_due_jobs() == 1 and RESULTS == ["s", "a"]
    assert scheduler.job_map == {}
    assert scheduler.seconds_until_next_job(default=1.0) == 1.0


@pytest.mark.anyio
async def test_recurring_job_is_rescheduled(clock):
    scheduler = Scheduler(now=clock)
    job = ScheduledJob(sync_job, ("tick",), schedule="* * * * *", now=clock())
    scheduler.add_job(job)
    for _ in range(3):
        clock.advance(minutes=1)
        await scheduler.run_due_jobs()
    assert RESULTS == ["tick"] * 3
    assert job.next_run == clock() + datetime.timedelta(minutes=1)
    assert scheduler.seconds_until_next_job() == 60.0


@pytest.mark.anyio
async def test_removed_job_does_not_run(clock):
    scheduler = Scheduler(now=clock)
    job = ScheduledJob(sync_job, schedule=clock())
    scheduler.add_job(job)
    assert scheduler.remove_job(job.id) is job
    assert scheduler.remove_job(job.id) is None
    assert await scheduler.run_due_jobs() == 0


@pytest.mark.anyio
async def test_a_job_may_add_jobs_while_running(clock):
    """Jobs run outside the scheduler lock, so they can schedule more work."""
    scheduler = Scheduler(now=clock)

    def spawner():
        scheduler.add_job(ScheduledJob(sync_job, ("child",), schedule=clock()))

    scheduler.add_job(ScheduledJob(spawner, schedule=clock()))
    assert await scheduler.run_due_jobs() == 2
    assert RESULTS == ["child"]


@pytest.mark.anyio
async def test_save_and_load(tmp_path, clock):
    path = str(tmp_path / "schedule.json")
    scheduler = Scheduler(schedule_file=path, allowed_modules=[THIS_MODULE], now=clock)
    scheduler.add_job(ScheduledJob(sync_job, ("later",), schedule=clock() + datetime.timedelta(hours=1), id="one"))
    scheduler.add_job(ScheduledJob(async_job, ("cron",), schedule="0 * * * *", id="two", now=clock()))

    reloaded = Scheduler(schedule_file=path, allowed_modules=[THIS_MODULE], now=clock)
    assert sorted(reloaded.job_map) == ["one", "two"]
    clock.advance(hours=1)
    assert await reloaded.run_due_jobs() == 2
    assert sorted(RESULTS) == ["cron", "later"]
    assert sorted(orjson.loads((tmp_path / "schedule.json").read_bytes()), key=lambda j: j["id"])[0]["schedule"] == "0 * * * *"


@pytest.mark.anyio
async def test_start_runs_due_jobs_in_real_time():
    scheduler = Scheduler()
    scheduler.add_job(ScheduledJob(sync_job, ("live",), schedule=datetime.datetime.now()))
    async with anyio.create_task_group() as task_group:
        await scheduler.start(task_group)
        with anyio.fail_after(2):
            while not RESULTS:
                await anyio.sleep(0.01)
        await scheduler.stop()
    assert RESULTS == ["live"]


# --- CLI ---------------------------------------------------------------------

def test_cli_add_list_remove(tmp_path):
    runner, path = CliRunner(), str(tmp_path / "s.json")
    added = runner.invoke(app, ["-f", path, "-m", THIS_MODULE, "add", f"{THIS_MODULE}.sync_job", "*/5 * * * *"])
    assert added.exit_code == 0, added.output
    job_id = added.output.split()[2]
    listed = runner.invoke(app, ["-f", path, "-m", THIS_MODULE, "list"])
    assert job_id in listed.output and "sync_job" in listed.output
    assert runner.invoke(app, ["-f", path, "-m", THIS_MODULE, "remove", job_id]).exit_code == 0
    assert "No jobs" in runner.invoke(app, ["-f", path, "-m", THIS_MODULE, "list"]).output


def test_cli_refuses_functions_outside_allowed_modules(tmp_path):
    result = CliRunner().invoke(app, ["-f", str(tmp_path / "s.json"), "add", "os.system", "* * * * *"])
    assert result.exit_code == 1
    assert "allowed_modules" in result.output


def test_cli_refuses_to_load_a_file_naming_disallowed_functions(tmp_path):
    path = tmp_path / "s.json"
    path.write_bytes(orjson.dumps([{"id": "x", "func": "os.system", "args": [], "kwargs": {}, "schedule": "* * * * *"}]))
    result = CliRunner().invoke(app, ["-f", str(path), "list"])
    assert result.exit_code == 2


def test_a_scheduler_with_a_file_refuses_jobs_it_could_not_reload(tmp_path):
    scheduler = Scheduler(schedule_file=str(tmp_path / "s.json"))
    def nested():
        return None

    for unsaveable in (lambda: None, nested, ScheduledJob.to_dict):  # a lambda, a nested function, a method
        with pytest.raises(ValueError, match="module-level"):
            scheduler.add_job(ScheduledJob(unsaveable, schedule="* * * * *"))
    Scheduler().add_job(ScheduledJob(lambda: None, schedule="* * * * *"))  # without a file it is fine
