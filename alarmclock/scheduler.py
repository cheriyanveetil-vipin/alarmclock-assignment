"""Foreground loop that watches the clock and rings due alarms."""

from __future__ import annotations

import sys
import time as time_mod
from datetime import datetime, timedelta

from .models import Alarm
from .storage import Store

RING_BEEPS = 6
RING_INTERVAL_SECONDS = 1
SNOOZE_MINUTES = 5


def _beep(times: int = RING_BEEPS) -> None:
    for _ in range(times):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time_mod.sleep(RING_INTERVAL_SECONDS)


def _ring(alarm: Alarm, store: Store, alarms: list[Alarm]) -> None:
    label = f" - {alarm.label}" if alarm.label else ""
    print(f"\n⏰ ALARM {alarm.time_str}{label}")
    _beep()
    try:
        choice = input("Press Enter to dismiss, or 's' + Enter to snooze 5 min: ").strip().lower()
    except EOFError:
        choice = ""

    today = datetime.now().date().isoformat()

    if choice == "s":
        snooze_time = datetime.now() + timedelta(minutes=SNOOZE_MINUTES)
        snoozed = Alarm.new(
            time_value=f"{snooze_time.hour:02d}:{snooze_time.minute:02d}",
            label=f"{alarm.label} (snoozed)".strip(" -") if alarm.label else "snoozed",
            repeat_value=None,
            existing=alarms,
        )
        alarms.append(snoozed)
        print(f"Snoozed until {snoozed.time_str}.")
    else:
        print("Dismissed.")

    alarm.last_triggered = today
    if not alarm.repeat:
        alarm.enabled = False

    store.save(alarms)


def run(store: Store, poll_seconds: float = 1.0) -> None:
    print("Alarm clock running. Press Ctrl+C to stop.")
    try:
        while True:
            alarms = store.load()
            now = datetime.now()
            due = [a for a in alarms if a.matches(now)]
            for alarm in due:
                _ring(alarm, store, alarms)
            time_mod.sleep(poll_seconds)
    except KeyboardInterrupt:
        print("\nStopped.")
