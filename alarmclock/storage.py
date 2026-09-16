"""JSON-file persistence for alarms."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Alarm

DEFAULT_PATH = Path(os.environ.get("ALARMCLOCK_HOME", Path.home() / ".alarmclock")) / "alarms.json"


class Store:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_PATH

    def load(self) -> list[Alarm]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return []
        return [Alarm.from_dict(item) for item in raw]

    def save(self, alarms: list[Alarm]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [a.to_dict() for a in alarms]
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.path)
