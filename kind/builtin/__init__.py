"""Builtin mixins: path finding, time dimension and Graphviz rendering, attached to every Kind."""
import logging

from kind.builtin import visual
from kind.builtin.path import KindPathMixin
from kind.builtin.time_dim import KindTimeDimMixin
from kind.builtin.timeline import Timeline
from kind.builtin.visual import KindRender
from kind.core.mixinability import register_mixin

log = logging.getLogger(__name__)

__all__ = ["apply_builtins", "BUILTIN_MIXINS", "KindPathMixin", "KindTimeDimMixin", "KindRender", "Timeline"]

BUILTIN_MIXINS = {
    **{name: getattr(KindPathMixin, name) for name in ('path_to', 'match')},
    **{name: getattr(KindTimeDimMixin, name) for name in (
        'time_head', 'time_tail', 'as_date', 'as_time', 'as_datetime', 'day', 'hour', 'minute', 'second',
        'period', 'as_period', 'duration', 'as_duration', 'delta', 'as_delta')},
    **{renderer.__name__: renderer for renderer in visual.RENDERERS},
    'from_mmd': staticmethod(visual.from_mmd),
}


def apply_builtins() -> None:
    """Registers every builtin mixin; idempotent (re-registering replaces the same mixin)."""
    applied = sum(register_mixin(value, name) for name, value in BUILTIN_MIXINS.items())
    log.debug(f"Applied {applied} of {len(BUILTIN_MIXINS)} builtin mixins.")
