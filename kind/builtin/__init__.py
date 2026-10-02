from core.mixinability import register_mixin
from .path import KindPathMixin
from .time_dim import KindTimeDimMixin
from .visual import KindRender
from .timeline import Timeline
import logging

log = logging.getLogger(__name__)

def apply_builtins():
    successful_mixins = 0
    total_mixins = 0

    # Path Mixin
    total_mixins += 1
    if register_mixin(KindPathMixin.path_to, 'path_to'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindPathMixin.match, 'match'): successful_mixins += 1

    # Time Dimension Mixin
    
    
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.time_head, 'time_head'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.time_tail, 'time_tail'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.as_date, 'as_date'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.as_time, 'as_time'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.as_datetime, 'as_datetime'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.day, 'day'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.hour, 'hour'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.minute, 'minute'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.second, 'second'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.period, 'period'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.as_period, 'as_period'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.duration, 'duration'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.as_duration, 'as_duration'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.delta, 'delta'): successful_mixins += 1
    total_mixins += 1
    if register_mixin(KindTimeDimMixin.as_delta, 'as_delta'): successful_mixins += 1

    # Visual Mixin
    visual_methods = [
        'to_dot', 'a_to_svg', 'to_svg', 'a_to_png', 'to_png', 'to_mmd', 'to_ascii'
    ]
    for method_name in visual_methods:
        total_mixins += 1
        if register_mixin(getattr(KindRender, method_name), method_name): successful_mixins += 1

    log.debug(f"Mixin application complete. Successfully applied {successful_mixins} of {total_mixins} mixins.")
