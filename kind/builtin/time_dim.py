"""This module gives Kinds a time dimension: a Kind named like an ISO 8601 date or time.

`kind.as_date`, `kind.hour`, ... read the time from the name and raise ValueError when
the name is not a date or time. `kind.time_head` / `kind.time_tail` are views over every
pooled Kind that *is* a date or time, earliest or latest first. A view offers four kinds of
operation, each named for what it returns:

- filters      `filter_by_*`                         -> a narrower view
- selectors    first, last, nth, closest, furthest  -> one Kind
- reshapers    reversed, shuffled, sample, unique    -> a view in another order or size
- aggregates   map, reduce, sum, min, max, average, median, mode, std, variance,
               percentile, quantile, count, is_empty, any, all, none, span -> a value
"""
from __future__ import annotations

import datetime
import random
import statistics
from collections import Counter
from functools import reduce as fold
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Optional, Union

if TYPE_CHECKING:
    from kind.core.kind import Kind

Moment = Union['Kind', datetime.datetime]


def parse_timestamp(name: str) -> Optional[datetime.datetime]:
    """The datetime an ISO 8601 name denotes (a date means midnight), or None."""
    try:
        return datetime.datetime.fromisoformat(name)
    except ValueError:
        return None


def when(kind: 'Kind') -> datetime.datetime:
    """The datetime of a temporal Kind; ValueError for any other Kind."""
    moment = parse_timestamp(kind.name)
    if moment is None:
        raise ValueError(f"Kind {kind.name!r} is not a date or time. "
                         f"Hint: time properties need an ISO 8601 name such as '2026-10-02' or '2026-10-02T13:45:00'.")
    return moment


def _moment(value: Moment) -> datetime.datetime:
    return value if isinstance(value, datetime.datetime) else when(value)


class KindTimeDimMixin:
    _parse_timestamp = staticmethod(lambda kind: parse_timestamp(kind.name))

    @staticmethod
    def _temporal_kinds(kinds: Iterable['Kind']) -> list['Kind']:
        return sorted((k for k in kinds if parse_timestamp(k.name) is not None), key=when)

    @property
    def time_head(self) -> 'KindHeadTailView':
        """Every pooled temporal Kind, earliest first."""
        return KindHeadTailView(KindTimeDimMixin._temporal_kinds(type(self)._numbered))

    @property
    def time_tail(self) -> 'KindHeadTailView':
        """Every pooled temporal Kind, latest first."""
        return self.time_head.reversed()

    @property
    def as_date(self) -> datetime.date:
        return when(self).date()

    @property
    def as_time(self) -> datetime.time:
        return when(self).time()

    @property
    def as_datetime(self) -> datetime.datetime:
        return when(self)

    @property
    def day(self) -> int:
        return when(self).day

    @property
    def hour(self) -> int:
        return when(self).hour

    @property
    def minute(self) -> int:
        return when(self).minute

    @property
    def second(self) -> int:
        return when(self).second

    @property
    def period(self) -> datetime.timedelta:
        """Time from the earliest to the latest pooled temporal Kind."""
        return self.time_head.span()

    as_period = duration = as_duration = delta = as_delta = period


class KindHeadTailView:
    """An ordered view over temporal Kinds."""

    def __init__(self, items: Iterable['Kind']):
        self._items = list(items)

    def __getitem__(self, item):
        return self._items[item]

    def __iter__(self) -> Iterator['Kind']:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def _where(self, predicate: Callable[[datetime.datetime], bool]) -> 'KindHeadTailView':
        return KindHeadTailView(k for k in self._items if predicate(when(k)))

    # --- span -----------------------------------------------------------------

    def span(self) -> datetime.timedelta:
        """Time from the first to the last item (zero for fewer than two)."""
        return when(self._items[-1]) - when(self._items[0]) if self._items else datetime.timedelta(0)

    period = as_period = property(span)

    @property
    def days(self) -> int:
        return self.span().days

    @property
    def seconds(self) -> int:
        return self.span().seconds

    # --- filters: a narrower view --------------------------------------------

    def filter_by_year(self, year: int) -> 'KindHeadTailView':
        return self._where(lambda t: t.year == year)

    def filter_by_month(self, year: int, month: int) -> 'KindHeadTailView':
        return self._where(lambda t: (t.year, t.month) == (year, month))

    def filter_by_day(self, year: int, month: int, day: int) -> 'KindHeadTailView':
        return self._where(lambda t: (t.year, t.month, t.day) == (year, month, day))

    def filter_by_hour(self, year: int, month: int, day: int, hour: int) -> 'KindHeadTailView':
        return self._where(lambda t: (t.year, t.month, t.day, t.hour) == (year, month, day, hour))

    def filter_by_minute(self, year: int, month: int, day: int, hour: int, minute: int) -> 'KindHeadTailView':
        return self._where(lambda t: (t.year, t.month, t.day, t.hour, t.minute) == (year, month, day, hour, minute))

    def filter_by_second(self, year: int, month: int, day: int, hour: int, minute: int, second: int) -> 'KindHeadTailView':
        return self._where(lambda t: (t.year, t.month, t.day, t.hour, t.minute, t.second)
                           == (year, month, day, hour, minute, second))

    def filter_by_weekday(self, weekday: int) -> 'KindHeadTailView':
        """Monday is 0, Sunday is 6."""
        return self._where(lambda t: t.weekday() == weekday)

    def filter_by_week_of_year(self, week_of_year: int) -> 'KindHeadTailView':
        return self._where(lambda t: t.isocalendar()[1] == week_of_year)

    def filter_by_quarter(self, quarter: int) -> 'KindHeadTailView':
        return self._where(lambda t: (t.month - 1) // 3 + 1 == quarter)

    def filter_by_time_of_day(self, time_of_day: str) -> 'KindHeadTailView':
        """morning 5–12, afternoon 12–17, evening 17–21, night 21–5."""
        hours = {'morning': range(5, 12), 'afternoon': range(12, 17), 'evening': range(17, 21),
                 'night': [*range(21, 24), *range(0, 5)]}
        if time_of_day not in hours:
            raise ValueError(f"Unknown time of day {time_of_day!r}; expected one of {sorted(hours)}")
        return self._where(lambda t: t.hour in hours[time_of_day])

    def filter_by_leap_year(self, is_leap_year: bool) -> 'KindHeadTailView':
        return self._where(lambda t: _is_leap(t.year) == is_leap_year)

    def filter_by_start_of_month(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.day == 1)

    def filter_by_end_of_month(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.day == _days_in_month(t.year, t.month))

    def filter_by_start_of_year(self) -> 'KindHeadTailView':
        return self._where(lambda t: (t.month, t.day) == (1, 1))

    def filter_by_end_of_year(self) -> 'KindHeadTailView':
        return self._where(lambda t: (t.month, t.day) == (12, 31))

    def filter_by_start_of_quarter(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.month in (1, 4, 7, 10) and t.day == 1)

    def filter_by_end_of_quarter(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.month in (3, 6, 9, 12) and t.day == _days_in_month(t.year, t.month))

    def filter_by_start_of_week(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.weekday() == 0)

    def filter_by_end_of_week(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.weekday() == 6)

    def filter_by_weekend(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.weekday() >= 5)

    def filter_by_workday(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.weekday() < 5)

    def filter_by_yesterday(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.date() == datetime.date.today() - datetime.timedelta(days=1))

    def filter_by_today(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.date() == datetime.date.today())

    def filter_by_tomorrow(self) -> 'KindHeadTailView':
        return self._where(lambda t: t.date() == datetime.date.today() + datetime.timedelta(days=1))

    def filter_by_future(self) -> 'KindHeadTailView':
        now = datetime.datetime.now()
        return self._where(lambda t: t > now)

    def filter_by_past(self) -> 'KindHeadTailView':
        now = datetime.datetime.now()
        return self._where(lambda t: t < now)

    def filter_by_same_day(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: t.date() == other.date())

    def filter_by_same_month(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: (t.year, t.month) == (other.year, other.month))

    def filter_by_same_year(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: t.year == other.year)

    def filter_by_same_quarter(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: (t.year, (t.month - 1) // 3) == (other.year, (other.month - 1) // 3))

    def filter_by_same_week(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: t.isocalendar()[:2] == other.isocalendar()[:2])

    def filter_by_same_weekday(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: t.weekday() == other.weekday())

    def filter_by_same_time(self, other: Moment) -> 'KindHeadTailView':
        other = _moment(other)
        return self._where(lambda t: t.time() == other.time())

    def filter_by_between(self, start: Moment, end: Moment) -> 'KindHeadTailView':
        start, end = _moment(start), _moment(end)
        return self._where(lambda t: start <= t <= end)

    # --- selectors: one Kind --------------------------------------------------

    def first(self) -> 'Kind':
        return self._items[0]

    def last(self) -> 'Kind':
        return self._items[-1]

    def nth(self, n: int) -> 'Kind':
        return self._items[n]

    def closest(self, other: Moment) -> 'Kind':
        other = _moment(other)
        return min(self._items, key=lambda k: abs(when(k) - other))

    def furthest(self, other: Moment) -> 'Kind':
        other = _moment(other)
        return max(self._items, key=lambda k: abs(when(k) - other))

    # --- reshapers: another view ----------------------------------------------

    def reversed(self) -> 'KindHeadTailView':
        return KindHeadTailView(self._items[::-1])

    def shuffled(self) -> 'KindHeadTailView':
        return KindHeadTailView(random.sample(self._items, len(self._items)))

    def sample(self, n: int) -> 'KindHeadTailView':
        return KindHeadTailView(random.sample(self._items, n))

    def unique(self) -> 'KindHeadTailView':
        return KindHeadTailView(dict.fromkeys(self._items))

    # --- aggregates: a value over fn(kind) ------------------------------------

    def map(self, fn: Callable[['Kind'], Any]) -> list:
        return [fn(k) for k in self._items]

    def reduce(self, fn: Callable[[Any, 'Kind'], Any], initial: Any) -> Any:
        return fold(fn, self._items, initial)

    def sum(self, fn: Callable[['Kind'], Any]) -> Any:
        return sum(self.map(fn))

    def max(self, fn: Callable[['Kind'], Any]) -> Any:
        return max(self.map(fn))

    def min(self, fn: Callable[['Kind'], Any]) -> Any:
        return min(self.map(fn))

    def average(self, fn: Callable[['Kind'], Any]) -> Any:
        return statistics.fmean(self.map(fn))

    def median(self, fn: Callable[['Kind'], Any]) -> Any:
        return statistics.median(self.map(fn))

    def mode(self, fn: Callable[['Kind'], Any]) -> list:
        counts = Counter(self.map(fn))
        top = max(counts.values())
        return [value for value, count in counts.items() if count == top]

    def std(self, fn: Callable[['Kind'], Any]) -> float:
        return statistics.pstdev(self.map(fn))

    def variance(self, fn: Callable[['Kind'], Any]) -> float:
        return statistics.pvariance(self.map(fn))

    def percentile(self, fn: Callable[['Kind'], Any], percentile: float) -> Any:
        return self.quantile(fn, percentile / 100)

    def quantile(self, fn: Callable[['Kind'], Any], quantile: float) -> Any:
        """Linear interpolation between closest ranks (numpy's default)."""
        values = sorted(self.map(fn))
        position = (len(values) - 1) * quantile
        lower = int(position)
        upper = min(lower + 1, len(values) - 1)
        return values[lower] + (values[upper] - values[lower]) * (position - lower)

    def count(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def any(self, predicate: Callable[['Kind'], bool]) -> bool:
        return any(predicate(k) for k in self._items)

    def all(self, predicate: Callable[['Kind'], bool]) -> bool:
        return all(predicate(k) for k in self._items)

    def none(self, predicate: Callable[['Kind'], bool]) -> bool:
        return not self.any(predicate)


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        return 29 if _is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31
