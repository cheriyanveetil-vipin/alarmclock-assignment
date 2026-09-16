"""Alarm data model and repeat-schedule logic."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, time as dtime
import itertools
import re

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri"]
WEEKENDS = ["sat", "sun"]

_id_counter = itertools.count(1)


class InvalidAlarmError(ValueError):
    pass


def parse_time(value: str) -> dtime:
    match = TIME_RE.match(value.strip())
    if not match:
        raise InvalidAlarmError(f"Invalid time {value!r}; expected 24h HH:MM, e.g. 07:30")
    hour, minute = int(match.group(1)), int(match.group(2))
    return dtime(hour=hour, minute=minute)


def parse_repeat(value: str) -> list[str]:
    """Normalize a --repeat value into a sorted list of day abbreviations.

    Empty list means "once" (fires the next time the clock hits that HH:MM,
    then disables itself).
    """
    if value is None:
        return []
    value = value.strip().lower()
    if value in ("", "once", "none"):
        return []
    if value == "daily":
        return list(DAY_NAMES)
    if value == "weekdays":
        return list(WEEKDAYS)
    if value == "weekends":
        return list(WEEKENDS)
    days = [d.strip()[:3] for d in value.split(",") if d.strip()]
    unknown = [d for d in days if d not in DAY_NAMES]
    if unknown:
        raise InvalidAlarmError(
            f"Unknown day(s) {unknown}; use mon/tue/wed/thu/fri/sat/sun, "
            "or once/daily/weekdays/weekends"
        )
    # de-dupe, keep canonical order
    return [d for d in DAY_NAMES if d in days]


@dataclass
class Alarm:
    id: int
    hour: int
    minute: int
    label: str = ""
    repeat: list[str] = field(default_factory=list)  # [] => one-shot
    enabled: bool = True
    last_triggered: str | None = None  # ISO date of last fire, to avoid double-ring

    @property
    def time_str(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    @property
    def repeat_str(self) -> str:
        if not self.repeat:
            return "once"
        if self.repeat == DAY_NAMES:
            return "daily"
        if self.repeat == WEEKDAYS:
            return "weekdays"
        if self.repeat == WEEKENDS:
            return "weekends"
        return ",".join(self.repeat)

    def matches(self, now: datetime) -> bool:
        if not self.enabled:
            return False
        if now.hour != self.hour or now.minute != self.minute:
            return False
        today = now.date().isoformat()
        if self.last_triggered == today:
            return False
        if self.repeat:
            return DAY_NAMES[now.weekday()] in self.repeat
        return True

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Alarm":
        return Alarm(
            id=data["id"],
            hour=data["hour"],
            minute=data["minute"],
            label=data.get("label", ""),
            repeat=list(data.get("repeat", [])),
            enabled=data.get("enabled", True),
            last_triggered=data.get("last_triggered"),
        )

    @staticmethod
    def next_id(existing: list["Alarm"]) -> int:
        used = {a.id for a in existing}
        candidate = 1
        while candidate in used:
            candidate += 1
        return candidate

    @classmethod
    def new(cls, time_value: str, label: str = "", repeat_value: str | None = None,
             existing: list["Alarm"] | None = None) -> "Alarm":
        t = parse_time(time_value)
        repeat = parse_repeat(repeat_value)
        existing = existing or []
        return cls(
            id=cls.next_id(existing),
            hour=t.hour,
            minute=t.minute,
            label=label,
            repeat=repeat,
        )
