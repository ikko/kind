"""This module defines the protocols that govern the behavior of Kind objects.

These protocols establish a clear contract for extending the Kind class with new functionality,
promoting a clean and maintainable architecture.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Iterator, List, Optional, Protocol, Union, Callable, Awaitable, runtime_checkable
import datetime



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
    def head(self) -> Any:
        """Returns a view of Kinds sorted chronologically (earliest first)."""
        ...

    @property
    @abstractmethod
    def tail(self) -> Any:
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

    @abstractmethod
    def to_mmd(self, mode: str = "tree") -> str:
        """Generates a Mermaid diagram string representation of the Kind graph."""
        ...

    @abstractmethod
    def to_ascii(self, mode: str = "tree") -> str:
        """Generates an ASCII art representation of the Kind graph."""
        ...


@runtime_checkable
class MixinFunction(Protocol):
    async def __call__(self, *args: Any, new_process: bool = False, new_thread: bool = True, **params: Any) -> Union[Any, Awaitable[Any]]:
        """Formal interface for mixin functions, supporting async, process/thread execution, and return type casting."""
        ...