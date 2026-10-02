import datetime
from kind import Kind
from kind.builtin.time_dim import KindTimeDimMixin



def test_parse_timestamp():
    # _parse_timestamp is now a static method, call it directly from the class
    # It expects a Kind instance as an argument

    # Test with valid ISO format datetime
    s1 = Kind("2023-01-15T10:30:00")
    dt1 = KindTimeDimMixin._parse_timestamp(s1)
    assert dt1 == datetime.datetime(2023, 1, 15, 10, 30, 0)

    # Test with valid ISO format date (time defaults to 00:00:00)
    s2 = Kind("2023-03-20")
    dt2 = KindTimeDimMixin._parse_timestamp(s2)
    assert dt2 == datetime.datetime(2023, 3, 20, 0, 0, 0)

    # A name that is not a date or time has no timestamp (no silent "today")
    assert KindTimeDimMixin._parse_timestamp(Kind("invalid-date")) is None

def test_kind_time_dim_properties():
    s_dt = Kind("2023-04-22T14:45:30")

    assert s_dt.as_date == datetime.date(2023, 4, 22)
    assert s_dt.as_time == datetime.time(14, 45, 30)
    assert s_dt.as_datetime == datetime.datetime(2023, 4, 22, 14, 45, 30)
    assert s_dt.day == 22
    assert s_dt.hour == 14
    assert s_dt.minute == 45
    assert s_dt.second == 30

    # Test with a date-only kind
    s_date_only = Kind("2023-05-01")
    assert s_date_only.as_date == datetime.date(2023, 5, 1)
    assert s_date_only.as_time == datetime.time(0, 0, 0)
    assert s_date_only.as_datetime == datetime.datetime(2023, 5, 1, 0, 0, 0)


