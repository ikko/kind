"""This module provides time_dim-related functionality for Kind objects.

It includes a mixin that adds properties for accessing the date and time components of a Kind's name,
as well as for calculating time periods and durations.
"""
from __future__ import annotations
import datetime
from typing import Iterator, Union, Any, Callable

class KindTimeDimMixin:
    @staticmethod
    def _parse_timestamp(s: 'Kind') -> datetime.datetime:
        try:
            return datetime.datetime.fromisoformat(s.name)
        except ValueError:
            return datetime.datetime.combine(datetime.date.today(), datetime.time.min)

    @staticmethod
    def _sorted_by_time(kind_cls: type['Kind']) -> list['Kind']:
        return sorted(kind_cls._numbered, key=lambda s: KindTimeDimMixin._parse_timestamp(s))

    @property
    def time_head(self) -> 'KindHeadTailView':
        # Pass the actual Kind class to the static method
        return KindHeadTailView(KindTimeDimMixin._sorted_by_time(self.__class__))

    @property
    def time_tail(self) -> 'KindHeadTailView':
        # Pass the actual Kind class to the static method
        return KindHeadTailView(KindTimeDimMixin._sorted_by_time(self.__class__)[::-1])

    @property
    def as_date(self) -> datetime.date:
        return KindTimeDimMixin._parse_timestamp(self).date()

    @property
    def as_time(self) -> datetime.time:
        return KindTimeDimMixin._parse_timestamp(self).time()

    @property
    def as_datetime(self) -> datetime.datetime:
        return KindTimeDimMixin._parse_timestamp(self)

    @property
    def day(self) -> int:
        return KindTimeDimMixin._parse_timestamp(self).day

    @property
    def hour(self) -> int:
        return KindTimeDimMixin._parse_timestamp(self).hour

    @property
    def minute(self) -> int:
        return KindTimeDimMixin._parse_timestamp(self).minute

    @property
    def second(self) -> int:
        return KindTimeDimMixin._parse_timestamp(self).second

    @property
    def period(self) -> datetime.timedelta:
        return self.time_head.period

    @property
    def as_period(self) -> datetime.timedelta:
        return self.time_head.as_period

    @property
    def duration(self) -> datetime.timedelta:
        return self.period

    @property
    def as_duration(self) -> datetime.timedelta:
        return self.as_period

    @property
    def delta(self) -> datetime.timedelta:
        return self.period

    @property
    def as_delta(self) -> datetime.timedelta:
        return self.as_period


class KindHeadTailView:
    def __init__(self, items: list['Kind']):
        self._items = items

    def __getitem__(self, item):
        return self._items[item]

    def __iter__(self) -> Iterator['Kind']:
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    @property
    def period(self) -> datetime.timedelta:
        if not self._items:
            return datetime.timedelta(0)
        start = KindTimeDimMixin._parse_timestamp(self._items[0])
        end = KindTimeDimMixin._parse_timestamp(self._items[-1])
        return end - start

    @property
    def as_period(self) -> datetime.timedelta:
        return self.period

    @property
    def days(self) -> int:
        return self.period.days

    @property
    def seconds(self) -> int:
        return self.period.seconds

    def filter_by_month(self, year: int, month: int) -> 'KindHeadTailView':
        result = [s for s in self._items
                  if KindTimeDimMixin._parse_timestamp(s).year == year and
                     KindTimeDimMixin._parse_timestamp(s).month == month]
        return KindHeadTailView(result)

    def filter_by_day(self, year: int, month: int, day: int) -> 'KindHeadTailView':
        result = [s for s in self._items
                  if KindTimeDimMixin._parse_timestamp(s).year == year and
                     KindTimeDimMixin._parse_timestamp(s).month == month and
                     KindTimeDimMixin._parse_timestamp(s).day == day]
        return KindHeadTailView(result)

    def filter_by_hour(self, year: int, month: int, day: int, hour: int) -> 'KindHeadTailView':
        result = [s for s in self._items
                  if KindTimeDimMixin._parse_timestamp(s).year == year and
                     KindTimeDimMixin._parse_timestamp(s).month == month and
                     KindTimeDimMixin._parse_timestamp(s).day == day and
                     KindTimeDimMixin._parse_timestamp(s).hour == hour]
        return KindHeadTailView(result)

    def filter_by_minute(self, year: int, month: int, day: int, hour: int, minute: int) -> 'KindHeadTailView':
        result = [s for s in self._items
                  if KindTimeDimMixin._parse_timestamp(s).year == year and
                     KindTimeDimMixin._parse_timestamp(s).month == month and
                     KindTimeDimMixin._parse_timestamp(s).day == day and
                     KindTimeDimMixin._parse_timestamp(s).hour == hour and
                     KindTimeDimMixin._parse_timestamp(s).minute == minute]
        return KindHeadTailView(result)

    def filter_by_second(self, year: int, month: int, day: int, hour: int, minute: int, second: int) -> 'KindHeadTailView':
        result = [s for s in self._items
                  if KindTimeDimMixin._parse_timestamp(s).year == year and
                     KindTimeDimMixin._parse_timestamp(s).month == month and
                     KindTimeDimMixin._parse_timestamp(s).day == day and
                     KindTimeDimMixin._parse_timestamp(s).hour == hour and
                     KindTimeDimMixin._parse_timestamp(s).minute == minute and
                     KindTimeDimMixin._parse_timestamp(s).second == second]
        return KindHeadTailView(result)

    def filter_by_weekday(self, weekday: int) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).weekday() == weekday]
        return KindHeadTailView(result)

    def filter_by_week_of_year(self, week_of_year: int) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).isocalendar()[1] == week_of_year]
        return KindHeadTailView(result)

    def filter_by_quarter(self, quarter: int) -> 'KindHeadTailView':
        result = [s for s in self._items if (KindTimeDimMixin._parse_timestamp(s).month - 1) // 3 + 1 == quarter]
        return KindHeadTailView(result)

    def filter_by_year(self, year: int) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).year == year]
        return KindHeadTailView(result)

    def filter_by_time_of_day(self, time_of_day: str) -> 'KindHeadTailView':
        # This is a bit more complex as datetime doesn't have a direct equivalent.
        # We can simulate this by checking the hour.
        result = []
        for s in self._items:
            hour = KindTimeDimMixin._parse_timestamp(s).hour
            if time_of_day == 'morning' and 5 <= hour < 12:
                result.append(s)
            elif time_of_day == 'afternoon' and 12 <= hour < 17:
                result.append(s)
            elif time_of_day == 'evening' and 17 <= hour < 21:
                result.append(s)
            elif time_of_day == 'night' and (21 <= hour or hour < 5):
                result.append(s)
        return KindHeadTailView(result)

    def filter_by_timezone(self, timezone: str) -> 'KindHeadTailView':
        # datetime objects are naive by default, so this is not directly supported.
        # We will return an empty list.
        return KindHeadTailView([])

    def filter_by_dst(self, is_dst: bool) -> 'KindHeadTailView':
        # datetime objects are naive by default, so this is not directly supported.
        # We will return an empty list.
        return KindHeadTailView([])

    def filter_by_leap_year(self, is_leap_year: bool) -> 'KindHeadTailView':
        result = [s for s in self._items if self._is_leap(KindTimeDimMixin._parse_timestamp(s).year) == is_leap_year]
        return KindHeadTailView(result)

    def _is_leap(self, year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def filter_by_start_of_month(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).day == 1]
        return KindHeadTailView(result)

    def filter_by_end_of_month(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).day == self._days_in_month(KindTimeDimMixin._parse_timestamp(s).year, KindTimeDimMixin._parse_timestamp(s).month)]
        return KindHeadTailView(result)

    def _days_in_month(self, year: int, month: int) -> int:
        if month == 2:
            return 29 if self._is_leap(year) else 28
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            return 31

    def filter_by_start_of_year(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).month == 1 and KindTimeDimMixin._parse_timestamp(s).day == 1]
        return KindHeadTailView(result)

    def filter_by_end_of_year(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).month == 12 and KindTimeDimMixin._parse_timestamp(s).day == 31]
        return KindHeadTailView(result)

    def filter_by_start_of_quarter(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).month in [1, 4, 7, 10] and KindTimeDimMixin._parse_timestamp(s).day == 1]
        return KindHeadTailView(result)

    def filter_by_end_of_quarter(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).month in [3, 6, 9, 12] and KindTimeDimMixin._parse_timestamp(s).day == self._days_in_month(KindTimeDimMixin._parse_timestamp(s).year, KindTimeDimMixin._parse_timestamp(s).month)]
        return KindHeadTailView(result)

    def filter_by_start_of_week(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).weekday() == 0]
        return KindHeadTailView(result)

    def filter_by_end_of_week(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).weekday() == 6]
        return KindHeadTailView(result)

    def filter_by_weekend(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).weekday() >= 5]
        return KindHeadTailView(result)

    def filter_by_weekday(self) -> 'KindHeadTailView':
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).weekday() < 5]
        return KindHeadTailView(result)

    def filter_by_yesterday(self) -> 'KindHeadTailView':
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).date() == yesterday]
        return KindHeadTailView(result)

    def filter_by_today(self) -> 'KindHeadTailView':
        today = datetime.date.today()
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).date() == today]
        return KindHeadTailView(result)

    def filter_by_tomorrow(self) -> 'KindHeadTailView':
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).date() == tomorrow]
        return KindHeadTailView(result)

    def filter_by_future(self) -> 'KindHeadTailView':
        now = datetime.datetime.now()
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s) > now]
        return KindHeadTailView(result)

    def filter_by_past(self) -> 'KindHeadTailView':
        now = datetime.datetime.now()
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s) < now]
        return KindHeadTailView(result)

    def filter_by_same_day(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).date() == other.date()]
        return KindHeadTailView(result)

    def filter_by_same_month(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).month == other.month and KindTimeDimMixin._parse_timestamp(s).year == other.year]
        return KindHeadTailView(result)

    def filter_by_same_year(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).year == other.year]
        return KindHeadTailView(result)

    def filter_by_same_quarter(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if (KindTimeDimMixin._parse_timestamp(s).month - 1) // 3 == (other.month - 1) // 3 and KindTimeDimMixin._parse_timestamp(s).year == other.year]
        return KindHeadTailView(result)

    def filter_by_same_week(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).isocalendar()[1] == other.isocalendar()[1] and KindTimeDimMixin._parse_timestamp(s).year == other.year]
        return KindHeadTailView(result)

    def filter_by_same_weekday(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).weekday() == other.weekday()]
        return KindHeadTailView(result)

    def filter_by_same_time(self, other: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        result = [s for s in self._items if KindTimeDimMixin._parse_timestamp(s).time() == other.time()]
        return KindHeadTailView(result)

    def filter_by_between(self, start: Union['Kind', datetime.datetime], end: Union['Kind', datetime.datetime]) -> 'KindHeadTailView':
        if isinstance(start, Kind):
            start = KindTimeDimMixin._parse_timestamp(start)
        if isinstance(end, Kind):
            end = KindTimeDimMixin._parse_timestamp(end)
        result = [s for s in self._items if start <= KindTimeDimMixin._parse_timestamp(s) <= end]
        return KindHeadTailView(result)

    def filter_by_closest(self, other: Union['Kind', datetime.datetime]) -> 'Kind':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        return min(self._items, key=lambda s: abs(KindTimeDimMixin._parse_timestamp(s) - other))

    def filter_by_furthest(self, other: Union['Kind', datetime.datetime]) -> 'Kind':
        if isinstance(other, Kind):
            other = KindTimeDimMixin._parse_timestamp(other)
        return max(self._items, key=lambda s: abs(KindTimeDimMixin._parse_timestamp(s) - other))

    def filter_by_average(self) -> datetime.datetime:
        if not self._items:
            return datetime.datetime.now()
        return datetime.datetime.fromtimestamp(sum(s._parse_timestamp().timestamp() for s in self._items) / len(self._items))

    def filter_by_median(self) -> datetime.datetime:
        if not self._items:
            return datetime.datetime.now()
        sorted_items = sorted(self._items, key=lambda s: s._parse_timestamp())
        mid = len(sorted_items) // 2
        if len(sorted_items) % 2 == 0:
            return datetime.datetime.fromtimestamp((sorted_items[mid - 1]._parse_timestamp().timestamp() + sorted_items[mid]._parse_timestamp().timestamp()) / 2)
        else:
            return sorted_items[mid]._parse_timestamp()

    def filter_by_mode(self) -> list[datetime.datetime]:
        if not self._items:
            return []
        from collections import Counter
        counts = Counter(s._parse_timestamp() for s in self._items)
        max_count = max(counts.values())
        return [dt for dt, count in counts.items() if count == max_count]

    def filter_by_range(self) -> datetime.timedelta:
        if not self._items:
            return datetime.timedelta(0)
        return self.period

    def filter_by_std(self) -> float:
        if not self._items:
            return 0.0
        import numpy as np
        return np.std([s._parse_timestamp().timestamp() for s in self._items])

    def filter_by_variance(self) -> float:
        if not self._items:
            return 0.0
        import numpy as np
        return np.var([s._parse_timestamp().timestamp() for s in self._items])

    def filter_by_percentile(self, percentile: int) -> datetime.datetime:
        if not self._items:
            return datetime.datetime.now()
        import numpy as np
        return datetime.datetime.fromtimestamp(np.percentile([s._parse_timestamp().timestamp() for s in self._items], percentile))

    def filter_by_quantile(self, quantile: float) -> datetime.datetime:
        if not self._items:
            return datetime.datetime.now()
        import numpy as np
        return datetime.datetime.fromtimestamp(np.quantile([s._parse_timestamp().timestamp() for s in self._items], quantile))

    def filter_by_first(self) -> 'Kind':
        return self._items[0]

    def filter_by_last(self) -> 'Kind':
        return self._items[-1]

    def filter_by_nth(self, n: int) -> 'Kind':
        return self._items[n]

    def filter_by_sample(self, n: int) -> 'KindHeadTailView':
        import random
        return KindHeadTailView(random.sample(self._items, n))

    def filter_by_shuffle(self) -> 'KindHeadTailView':
        import random
        shuffled = list(self._items)
        random.shuffle(shuffled)
        return KindHeadTailView(shuffled)

    def filter_by_reverse(self) -> 'KindHeadTailView':
        return KindHeadTailView(self._items[::-1])

    def filter_by_unique(self) -> 'KindHeadTailView':
        return KindHeadTailView(list(dict.fromkeys(self._items)))

    def filter_by_count(self) -> int:
        return len(self._items)

    def filter_by_is_empty(self) -> bool:
        return not self._items

    def filter_by_any(self, pred: Callable[['Kind'], bool]) -> bool:
        return any(pred(s) for s in self._items)

    def filter_by_all(self, pred: Callable[['Kind'], bool]) -> bool:
        return all(pred(s) for s in self._items)

    def filter_by_none(self, pred: Callable[['Kind'], bool]) -> bool:
        return not any(pred(s) for s in self._items)

    def filter_by_map(self, fn: Callable[['Kind'], Any]) -> list[Any]:
        return [fn(s) for s in self._items]

    def filter_by_reduce(self, fn: Callable[[Any, 'Kind'], Any], initial: Any) -> Any:
        from functools import reduce
        return reduce(fn, self._items, initial)

    def filter_by_sum(self, fn: Callable[['Kind'], Any]) -> Any:
        return sum(fn(s) for s in self._items)

    def filter_by_max(self, fn: Callable[['Kind'], Any]) -> Any:
        return max(fn(s) for s in self._items)

    def filter_by_min(self, fn: Callable[['Kind'], Any]) -> Any:
        return min(fn(s) for s in self._items)

    def filter_by_average(self, fn: Callable[['Kind'], Any]) -> Any:
        return sum(fn(s) for s in self._items) / len(self._items)

    def filter_by_median(self, fn: Callable[['Kind'], Any]) -> Any:
        import numpy as np
        return np.median([fn(s) for s in self._items])

    def filter_by_mode(self, fn: Callable[['Kind'], Any]) -> Any:
        from collections import Counter
        counts = Counter(fn(s) for s in self._items)
        max_count = max(counts.values())
        return [item for item, count in counts.items() if count == max_count]

    def filter_by_std(self, fn: Callable[['Kind'], Any]) -> Any:
        import numpy as np
        return np.std([fn(s) for s in self._items])

    def filter_by_variance(self, fn: Callable[['Kind'], Any]) -> Any:
        import numpy as np
        return np.var([fn(s) for s in self._items])

    def filter_by_percentile(self, fn: Callable[['Kind'], Any], percentile: int) -> Any:
        import numpy as np
        return np.percentile([fn(s) for s in self._items], percentile)

    def filter_by_quantile(self, fn: Callable[['Kind'], Any], quantile: float) -> Any:
        import numpy as np
        return np.quantile([fn(s) for s in self._items], quantile)

    def filter_by_first(self, fn: Callable[['Kind'], Any]) -> Any:
        return fn(self._items[0])

    def filter_by_last(self, fn: Callable[['Kind'], Any]) -> Any:
        return fn(self._items[-1])

    def filter_by_nth(self, fn: Callable[['Kind'], Any], n: int) -> Any:
        return fn(self._items[n])

    def filter_by_sample(self, fn: Callable[['Kind'], Any], n: int) -> list[Any]:
        import random
        return [fn(s) for s in random.sample(self._items, n)]

    def filter_by_shuffle(self, fn: Callable[['Kind'], Any]) -> list[Any]:
        import random
        shuffled = list(self._items)
        random.shuffle(shuffled)
        return [fn(s) for s in shuffled]

    def filter_by_reverse(self, fn: Callable[['Kind'], Any]) -> list[Any]:
        return [fn(s) for s in self._items[::-1]]

    def filter_by_unique(self, fn: Callable[['Kind'], Any]) -> list[Any]:
        return list(dict.fromkeys(fn(s) for s in self._items))

    def filter_by_count(self, fn: Callable[['Kind'], Any]) -> int:
        return len(list(fn(s) for s in self._items))

    def filter_by_is_empty(self, fn: Callable[['Kind'], Any]) -> bool:
        return not list(fn(s) for s in self._items)

    def filter_by_any(self, fn: Callable[['Kind'], Any], pred: Callable[[Any], bool]) -> bool:
        return any(pred(fn(s)) for s in self._items)

    def filter_by_all(self, fn: Callable[['Kind'], Any], pred: Callable[[Any], bool]) -> bool:
        return all(pred(fn(s)) for s in self._items)

    def filter_by_none(self, fn: Callable[['Kind'], Any], pred: Callable[[Any], bool]) -> bool:
        return not any(pred(fn(s)) for s in self._items)
