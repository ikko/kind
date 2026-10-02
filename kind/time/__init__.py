"""kind.time: Kinds named like ISO 8601 dates and times, opt in with `import kind.time`.

Importing this package attaches the time properties (`as_date`, `hour`, `period`, ...)
and the time views (`time_head`, `time_tail`) to every Kind. The core does not load it:
a Kind is not a date unless the application says its Kinds can be.
"""
import logging

from kind.core.mixinability import register_mixin
from kind.core.protocols import TIME_MIXINS
from kind.time.arithmetic import add_time_objects, subtract_time_objects
from kind.time.dim import KindHeadTailView, KindTimeDimMixin, parse_timestamp, when
from kind.time.timeline import Timeline

log = logging.getLogger(__name__)

__all__ = ["KindHeadTailView", "KindTimeDimMixin", "Timeline", "add_time_objects", "subtract_time_objects",
           "parse_timestamp", "when", "TIME_MIXINS", "enable"]



def enable() -> None:
    """Attaches the time mixins to every Kind; idempotent, and run once on import."""
    applied = sum(register_mixin(getattr(KindTimeDimMixin, name), name) for name in TIME_MIXINS)
    log.debug(f"Applied {applied} of {len(TIME_MIXINS)} time mixins.")


enable()
