# kind-scheduler

Runs Python callables once or on a cron schedule, and processes batches concurrently. A separate
distribution from [`kind`](../README.md): a Kind named like an ISO 8601 datetime can be a schedule,
but scheduling is not part of what a Kind is.

```bash
kind-scheduler -f jobs.json -m my_app.tasks add my_app.tasks.cleanup "*/5 * * * *"
kind-scheduler -f jobs.json -m my_app.tasks list
kind-scheduler -f jobs.json -m my_app.tasks run
```

A schedule file names functions by dotted path, and loading it imports code. So functions resolve only
from the modules given with `--allow-module` (`Scheduler(allowed_modules=...)` in Python); anything else
is refused with `CallableNotAllowedError`.

Documentation: [API reference](docs/api_reference.md) · [cookbook](docs/cookbook_scheduling_jobs.md) ·
[topic](docs/topic_scheduling/index.md).

Private, all rights reserved: see [LICENSE](LICENSE). Install from the checkout:
`uv pip install -e scheduler` (the `kind` it depends on resolves to `..`).
