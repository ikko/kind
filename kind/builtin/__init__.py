"""Builtin mixins attached to every Kind: path finding and Graphviz rendering (time is opt-in: kind.time)."""
import logging

from kind.builtin import visual
from kind.builtin.path import KindPathMixin
from kind.builtin.visual import KindRender
from kind.core.mixinability import register_mixin

log = logging.getLogger(__name__)

__all__ = ["apply_builtins", "BUILTIN_MIXINS", "KindPathMixin", "KindRender"]

BUILTIN_MIXINS = {
    **{name: getattr(KindPathMixin, name) for name in ('path_to', 'match')},
    **{renderer.__name__: renderer for renderer in visual.RENDERERS},
    'from_mmd': staticmethod(visual.from_mmd),
}


def apply_builtins() -> None:
    """Registers every builtin mixin; idempotent (re-registering replaces the same mixin)."""
    applied = sum(register_mixin(value, name) for name, value in BUILTIN_MIXINS.items())
    log.debug(f"Applied {applied} of {len(BUILTIN_MIXINS)} builtin mixins.")
