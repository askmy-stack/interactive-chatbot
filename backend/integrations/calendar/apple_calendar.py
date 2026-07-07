from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime

from backend.integrations.calendar.base import CalendarEvent, CalendarEventInput


class AppleCalendarProvider:
    """Reads and writes macOS Calendar events via AppleScript."""

    def get_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        if not shutil.which("osascript"):
            return []

        script = """
on run argv
  set startIso to item 1 of argv
  set endIso to item 2 of argv
  set py to "import json\\n"
  set py to py & "from datetime import datetime\\n"
  set py to py & "s=datetime.fromisoformat('" & startIso & "')\\n"
  set py to py & "e=datetime.fromisoformat('" & endIso & "')\\n"
  set py to py & "print(s.strftime('%A, %B %d, %Y %H:%M:%S'))\\n"
  set startHuman to do shell script "python3 - <<'PY'\\n" & py & "PY"
  set py2 to "import json\\n"
  set py2 to py2 & "from datetime import datetime\\n"
  set py2 to py2 & "e=datetime.fromisoformat('" & endIso & "')\\n"
  set py2 to py2 & "print(e.strftime('%A, %B %d, %Y %H:%M:%S'))\\n"
  set endHuman to do shell script "python3 - <<'PY'\\n" & py2 & "PY"
  tell application "Calendar"
    set out to "["
    set firstItem to true
    repeat with c in calendars
      set evs to every event of c whose start date ≥ date startHuman and start date < date endHuman
      repeat with ev in evs
        if not firstItem then set out to out & ","
        set firstItem to false
        set t to my esc(summary of ev)
        set st to my esc((start date of ev) as «class isot» as string)
        set en to my esc((end date of ev) as «class isot» as string)
        set caln to my esc(name of c)
        set eid to my esc(id of ev as string)
        set out to out & "{\\"title\\":\\"" & t & "\\",\\"start\\":\\"" & st & "\\",\\"end\\":\\"" & en & "\\",\\"calendar\\":\\"" & caln & "\\",\\"event_id\\":\\"" & eid & "\\"}"
      end repeat
    end repeat
    set out to out & "]"
    return out
  end tell
end run

on esc(s)
  set t to s as text
  set AppleScript's text item delimiters to "\\""
  set parts to text items of t
  set AppleScript's text item delimiters to "\\\\\\""
  set t to parts as text
  set AppleScript's text item delimiters to ""
  return t
end esc
"""
        try:
            proc = subprocess.run(
                ["osascript", "-", start.isoformat(), end.isoformat()],
                input=script,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return []

        if proc.returncode != 0:
            return []

        rows = json.loads(proc.stdout.strip() or "[]")
        events: list[CalendarEvent] = []
        for row in rows:
            events.append(
                CalendarEvent(
                    start=datetime.fromisoformat(row["start"]),
                    end=datetime.fromisoformat(row["end"]),
                    title=row["title"],
                    calendar=row.get("calendar"),
                    event_id=row.get("event_id"),
                )
            )
        return sorted(events, key=lambda e: e.start)

    def create_event(self, event: CalendarEventInput) -> str:
        if not shutil.which("osascript"):
            raise RuntimeError("osascript not available")

        cal_name = event.calendar or "Calendar"
        script = f'''
tell application "Calendar"
  set targetCal to first calendar whose name is "{cal_name}"
  set newEvent to make new event at end of events of targetCal with properties {{summary:"{event.title}", start date:date "{event.start.strftime("%A, %B %d, %Y %I:%M:%S %p")}", end date:date "{event.end.strftime("%A, %B %d, %Y %I:%M:%S %p")}"}}
  return id of newEvent as string
end tell
'''
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "create_event failed")
        return proc.stdout.strip()

    def update_event(self, event_id: str, event: CalendarEventInput) -> bool:
        if not shutil.which("osascript"):
            raise RuntimeError("osascript not available")

        script = f'''
tell application "Calendar"
  set targetEvent to first event whose id is {event_id}
  set summary of targetEvent to "{event.title}"
  set start date of targetEvent to date "{event.start.strftime("%A, %B %d, %Y %I:%M:%S %p")}"
  set end date of targetEvent to date "{event.end.strftime("%A, %B %d, %Y %I:%M:%S %p")}"
  return "ok"
end tell
'''
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0
