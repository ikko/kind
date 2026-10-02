"""This module provides `kind-scheduler`, a Typer CLI over a schedule file.

Functions are named by dotted path and are only imported from modules given with
--allow-module (repeatable): a schedule file is code to run, so it is opt-in per module.
"""
from typing import List, Optional

import anyio
import typer

from kind_scheduler.schedule import CallableNotAllowedError, ScheduledJob, Scheduler, resolve_callable

app = typer.Typer()
state: dict = {}


@app.callback()
def main(
    schedule_file: Optional[str] = typer.Option(None, "--schedule-file", "-f", help="The file where the schedule is stored."),
    allow_module: List[str] = typer.Option([], "--allow-module", "-m",
                                           help="A module whose functions jobs may run (repeatable)."),
):
    """Manage and run scheduled jobs."""
    try:
        state["scheduler"] = Scheduler(schedule_file=schedule_file, allowed_modules=allow_module)
    except CallableNotAllowedError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2)


@app.command()
def add(
    func_str: str = typer.Argument(..., help="The function to run, e.g. 'my_module.my_function'."),
    schedule: str = typer.Argument(..., help="Cron expression or ISO 8601 datetime."),
):
    """Adds a job to the schedule."""
    try:
        func = resolve_callable(func_str, state["scheduler"].allowed_modules)
        job = ScheduledJob(func=func, schedule=schedule)
    except (CallableNotAllowedError, ImportError, AttributeError, TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1)
    state["scheduler"].add_job(job)
    typer.echo(f"Added job {job.id} for '{func_str}' with schedule '{schedule}'")


@app.command()
def remove(job_id: str = typer.Argument(..., help="The ID of the job to remove.")):
    """Removes a job from the schedule."""
    if state["scheduler"].remove_job(job_id):
        typer.echo(f"Removed job {job_id}")
    else:
        typer.echo(f"Error: no job with ID '{job_id}'.", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_jobs():
    """Lists the jobs in the schedule."""
    jobs = state["scheduler"].job_map
    if not jobs:
        typer.echo("No jobs in the schedule.")
    for job_id, job in jobs.items():
        typer.echo(f"ID: {job_id}, Next Run: {job.next_run}, Schedule: {job.schedule}, Function: {job.func.__name__}")


@app.command()
def run():
    """Runs the scheduler until interrupted (Ctrl+C)."""
    scheduler = state["scheduler"]

    async def serve():
        async with anyio.create_task_group() as task_group:
            await scheduler.start(task_group)

    typer.echo("Scheduler started. Press Ctrl+C to exit.")
    try:
        anyio.run(serve)
    except KeyboardInterrupt:
        typer.echo("Scheduler stopped.")


if __name__ == "__main__":
    app()
