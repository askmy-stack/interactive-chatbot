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


class CalendarProvider(Protocol):
 def get_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
  """Return events in [start, end)."""

