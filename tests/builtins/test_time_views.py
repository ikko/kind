"""Every time-view filter, selector, reshaper and aggregate, against a hand-checked calendar."""
import datetime

import pytest

from kind import Kind
from kind.builtin.time_dim import KindHeadTailView
from kind.builtin.timeline import Timeline
from kind.core.time_arithmetics import add_time_objects, subtract_time_objects

# 2024 is a leap year; 2024-01-01 is a Monday.
NAMES = [
    "2024-01-01T08:00:00",  # Monday, start of year/quarter/month/week, morning
    "2024-01-06T13:00:00",  # Saturday, afternoon
    "2024-01-07T22:30:00",  # Sunday, end of week, night
    "2024-02-29T18:00:00",  # Thursday, leap day, end of month, evening
    "2024-03-31T09:15:30",  # Sunday, end of quarter/month
    "2023-12-31T23:59:59",  # Sunday, end of year (2023 not leap)
]


@pytest.fixture
def view():
    for name in NAMES:
        Kind(name)
    return Kind(NAMES[0]).time_head


def names(kinds):
    return sorted(kind.name[:10] for kind in kinds)


@pytest.mark.parametrize("call, expected", [
    (lambda v: v.filter_by_year(2023), ["2023-12-31"]),
    (lambda v: v.filter_by_month(2024, 1), ["2024-01-01", "2024-01-06", "2024-01-07"]),
    (lambda v: v.filter_by_day(2024, 2, 29), ["2024-02-29"]),
    (lambda v: v.filter_by_hour(2024, 1, 6, 13), ["2024-01-06"]),
    (lambda v: v.filter_by_minute(2024, 1, 7, 22, 30), ["2024-01-07"]),
    (lambda v: v.filter_by_second(2024, 3, 31, 9, 15, 30), ["2024-03-31"]),
    (lambda v: v.filter_by_weekday(3), ["2024-02-29"]),
    (lambda v: v.filter_by_week_of_year(1), ["2024-01-01", "2024-01-06", "2024-01-07"]),
    (lambda v: v.filter_by_quarter(1), ["2024-01-01", "2024-01-06", "2024-01-07", "2024-02-29", "2024-03-31"]),
    (lambda v: v.filter_by_time_of_day("morning"), ["2024-01-01", "2024-03-31"]),
    (lambda v: v.filter_by_time_of_day("afternoon"), ["2024-01-06"]),
    (lambda v: v.filter_by_time_of_day("evening"), ["2024-02-29"]),
    (lambda v: v.filter_by_time_of_day("night"), ["2023-12-31", "2024-01-07"]),
    (lambda v: v.filter_by_leap_year(False), ["2023-12-31"]),
    (lambda v: v.filter_by_start_of_month(), ["2024-01-01"]),
    (lambda v: v.filter_by_end_of_month(), ["2023-12-31", "2024-02-29", "2024-03-31"]),
    (lambda v: v.filter_by_start_of_year(), ["2024-01-01"]),
    (lambda v: v.filter_by_end_of_year(), ["2023-12-31"]),
    (lambda v: v.filter_by_start_of_quarter(), ["2024-01-01"]),
    (lambda v: v.filter_by_end_of_quarter(), ["2023-12-31", "2024-03-31"]),
    (lambda v: v.filter_by_start_of_week(), ["2024-01-01"]),
    (lambda v: v.filter_by_end_of_week(), ["2023-12-31", "2024-01-07", "2024-03-31"]),
    (lambda v: v.filter_by_weekend(), ["2023-12-31", "2024-01-06", "2024-01-07", "2024-03-31"]),
    (lambda v: v.filter_by_workday(), ["2024-01-01", "2024-02-29"]),
    (lambda v: v.filter_by_past(), sorted(n[:10] for n in NAMES)),
    (lambda v: v.filter_by_future(), []),
    (lambda v: v.filter_by_same_day(Kind("2024-02-29T00:00:00")), ["2024-02-29"]),
    (lambda v: v.filter_by_same_month(datetime.datetime(2024, 1, 15)), ["2024-01-01", "2024-01-06", "2024-01-07"]),
    (lambda v: v.filter_by_same_year(datetime.datetime(2023, 6, 1)), ["2023-12-31"]),
    (lambda v: v.filter_by_same_quarter(datetime.datetime(2024, 2, 1)), ["2024-01-01", "2024-01-06", "2024-01-07", "2024-02-29", "2024-03-31"]),
    (lambda v: v.filter_by_same_week(datetime.datetime(2024, 1, 3)), ["2024-01-01", "2024-01-06", "2024-01-07"]),
    (lambda v: v.filter_by_same_weekday(datetime.datetime(2024, 3, 3)), ["2023-12-31", "2024-01-07", "2024-03-31"]),
    (lambda v: v.filter_by_same_time(datetime.datetime(2000, 1, 1, 13, 0)), ["2024-01-06"]),
    (lambda v: v.filter_by_between(datetime.datetime(2024, 1, 2), Kind("2024-02-29T18:00:00")), ["2024-01-06", "2024-01-07", "2024-02-29"]),
])
def test_filters_return_the_matching_view(view, call, expected):
    result = call(view)
    assert isinstance(result, KindHeadTailView)
    assert names(result) == expected


def test_relative_day_filters_follow_the_clock():
    today = datetime.date.today()
    for offset in (-1, 0, 1):
        Kind((today + datetime.timedelta(days=offset)).isoformat())
    view = Kind(today.isoformat()).time_head
    assert [k.as_date for k in view.filter_by_yesterday()] == [today - datetime.timedelta(days=1)]
    assert [k.as_date for k in view.filter_by_today()] == [today]
    assert [k.as_date for k in view.filter_by_tomorrow()] == [today + datetime.timedelta(days=1)]


def test_unknown_time_of_day_is_refused(view):
    with pytest.raises(ValueError, match="time of day"):
        view.filter_by_time_of_day("brunch")


def test_selectors_reshapers_and_aggregates(view):
    second = lambda kind: kind.second
    assert view.first().name == "2023-12-31T23:59:59" and view.last().name.startswith("2024-03-31")
    assert view.nth(1).name.startswith("2024-01-01")
    assert view.furthest(datetime.datetime(2024, 1, 1)).name.startswith("2024-03-31")
    assert len(view.sample(2)) == 2 and sorted(view.shuffled(), key=lambda k: k.name) == sorted(view, key=lambda k: k.name)
    assert list(view.unique()) == list(view) and list(view.reversed()) == list(view)[::-1]
    assert view.map(second) == [59, 0, 0, 0, 0, 30]
    assert view.reduce(lambda total, kind: total + kind.second, 0) == 89
    assert (view.sum(second), view.min(second), view.max(second)) == (89, 0, 59)
    assert view.mode(second) == [0]
    values = [59, 0, 0, 0, 0, 30]
    mean = sum(values) / len(values)
    population_variance = sum((x - mean) ** 2 for x in values) / len(values)  # independent of statistics
    assert view.variance(second) == pytest.approx(population_variance)
    assert view.std(second) == pytest.approx(population_variance ** 0.5)
    assert (view.count(), view.is_empty(), KindHeadTailView([]).is_empty()) == (6, False, True)
    assert view.any(lambda k: k.day == 29) and view.all(lambda k: k.as_date.year >= 2023)
    assert view.none(lambda k: k.hour == 3)
    assert view.days == 90 and view.seconds == 9 * 3600 + 15 * 60 + 31  # 23:59:59 Dec 31 -> 09:15:30 Mar 31
    assert KindHeadTailView([]).span() == datetime.timedelta(0)


def test_timeline_ascii_marks_covered_days():
    d = lambda day: datetime.datetime(2026, 1, day)
    timeline = Timeline([(d(2), d(4)), (d(6), d(7))])
    assert timeline.to_ascii() == "##--#-"  # from the first day; a period's end is exclusive
    assert Timeline().to_ascii() == ""
    with pytest.raises(ValueError):
        Timeline([(d(3), d(2))])


@pytest.mark.parametrize("a, b, total", [
    (datetime.datetime(2026, 1, 1), datetime.timedelta(days=1), datetime.datetime(2026, 1, 2)),
    (datetime.timedelta(hours=1), datetime.datetime(2026, 1, 1), datetime.datetime(2026, 1, 1, 1)),
    (datetime.timedelta(hours=1), datetime.timedelta(hours=2), datetime.timedelta(hours=3)),
])
def test_add_time_objects(a, b, total):
    assert add_time_objects(a, b) == total


@pytest.mark.parametrize("a, b, difference", [
    (datetime.datetime(2026, 1, 2), datetime.timedelta(days=1), datetime.datetime(2026, 1, 1)),
    (datetime.datetime(2026, 1, 2), datetime.datetime(2026, 1, 1), datetime.timedelta(days=1)),
    (datetime.timedelta(hours=3), datetime.timedelta(hours=1), datetime.timedelta(hours=2)),
])
def test_subtract_time_objects(a, b, difference):
    assert subtract_time_objects(a, b) == difference


@pytest.mark.parametrize("operation", [add_time_objects, subtract_time_objects])
def test_time_arithmetic_refuses_other_types(operation):
    with pytest.raises(TypeError, match="Unsupported operand"):
        operation(datetime.datetime(2026, 1, 1), datetime.datetime(2026, 1, 2)) if operation is add_time_objects \
            else operation(datetime.timedelta(1), datetime.datetime(2026, 1, 1))
