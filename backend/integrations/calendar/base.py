from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class CalendarEvent:
    start: datetime
    end: datetime
    title: str
    calendar: str | None = None
    location: str | None = None
    is_all_day: bool = False
    event_id: str | None = None


@dataclass
class CalendarEventInput:
    title: str
    start: datetime
    end: datetime
    calendar: str | None = None
    location: str | None = None
    notes: str | None = None


class CalendarProvider(Protocol):
    def get_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        """Return events in [start, end)."""

    def create_event(self, event: CalendarEventInput) -> str:
        """Create an event and return its identifier."""

    def update_event(self, event_id: str, event: CalendarEventInput) -> bool:
        """Update an existing event by id."""
