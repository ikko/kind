"""This module defines the protocols that govern the behavior of Kind objects.

These protocols establish a clear contract for extending the Kind class with new functionality,
promoting a clean and maintainable architecture.
"""
from __future__ import annotations

import datetime
from abc import abstractmethod
from typing import Any, Callable, Iterator, List, Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kind.core.kind import Kind



class KindPathProtocol(Protocol):
    @abstractmethod
    def path_to(self, target: 'Kind') -> List['Kind']:

        """Finds a path from this Kind to a target Kind."""
        ...

    @abstractmethod
    def match(self, predicate: Callable[[Kind], bool], traversal: str = 'dfs') -> Iterator[Kind]:
        """Finds Kinds matching a predicate using specified traversal."""
        ...


class KindTimeDimProtocol(Protocol):
    @property
    @abstractmethod
    def time_head(self) -> Any:
        """Returns a view of Kinds sorted chronologically (earliest first)."""
        ...

    @property
    @abstractmethod
    def time_tail(self) -> Any:
        """Returns a view of Kinds sorted in reverse chronological order (latest first)."""
        ...

    @property
    @abstractmethod
    def as_date(self) -> datetime.date:
        """Returns the date part of the Kind's name as a date object."""
        ...

    @property
    @abstractmethod
    def as_time(self) -> datetime.time:
        """Returns the time part of the Kind's name as a time object."""
        ...

    @property
    @abstractmethod
    def as_datetime(self) -> datetime.datetime:
        """Returns the full datetime object parsed from the Kind's name."""
        ...

    @property
    @abstractmethod
    def day(self) -> int:
        """Returns the day component of the Kind's datetime."""
        ...

    @property
    @abstractmethod
    def hour(self) -> int:
        """Returns the hour component of the Kind's datetime."""
        ...

    @property
    @abstractmethod
    def minute(self) -> int:
        """Returns the minute component of the Kind's datetime."""
        ...

    @property
    @abstractmethod
    def second(self) -> int:
        """Returns the second component of the Kind's datetime."""
        ...

    @property
    @abstractmethod
    def period(self) -> datetime.timedelta:
        """Returns the time duration between the first and last Kinds in a sorted view."""
        ...

    @property
    @abstractmethod
    def as_period(self) -> datetime.timedelta:
        """Alias for the `period` property, returning the time duration."""
        ...

    @property
    @abstractmethod
    def duration(self) -> datetime.timedelta:
        """Alias for the `period` property, returning the time duration."""
        ...

    @property
    @abstractmethod
    def as_duration(self) -> datetime.timedelta:
        """Alias for the `as_period` property, returning the time duration."""
        ...

    @property
    @abstractmethod
    def delta(self) -> datetime.timedelta:
        """Alias for the `period` property, returning the time duration."""
        ...

    @property
    @abstractmethod
    def as_delta(self) -> datetime.timedelta:
        """Alias for the `as_period` property, returning the time duration."""
        ...


class KindVisualProtocol(Protocol):
    @abstractmethod
    def to_dot(self, mode: str = "tree") -> str:
        """Generates a DOT language string representation of the Kind graph."""
        ...

    @abstractmethod
    def to_svg(self, mode: str = "tree") -> str:
        """Renders the Kind graph to an SVG image string."""
        ...

    @abstractmethod
    def to_png(self, mode: str = "tree") -> bytes:
        """Renders the Kind graph to a PNG image as bytes."""
        ...
