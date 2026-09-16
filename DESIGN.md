# Design plan

## Requirements

An alarm clock CLI needs, at minimum:

- Set an alarm for a specific time.
- The alarm actually rings when that time comes, while the program is
  running.
- See what alarms are currently set.
- Remove or turn off an alarm.
- Support both one-time and repeating alarms (daily, weekdays, etc.) —
  this is the one piece of real "clock" logic that makes it more than a
  single timer.

Out of scope, kept simple on purpose: no background/daemon process, no
real audio (uses the terminal bell instead), no timezones, no database
or web UI.

## Design

Four small files, each with one job:

- `models.py` — the `Alarm` data model, time/repeat parsing, and the
  logic for "is this alarm due right now."
- `storage.py` — load/save alarms as a JSON file.
- `scheduler.py` — the `run` loop: check the clock every second, ring due
  alarms, handle dismiss/snooze.
- `cli.py` — command-line commands (`add`, `list`, `remove`, `enable`,
  `disable`, `clear`, `run`), each calling into the above.

Alarms are stored in a plain JSON file rather than a database, since a
handful of alarms doesn't need one. When an alarm fires, it beeps and
waits for the user to dismiss (Enter) or snooze (`s` + Enter) — one-shot
alarms then turn themselves off; repeating alarms wait for their next
scheduled day.

## Implementation plan

1. `models.py` first, with tests — this is where the actual alarm logic
   and edge cases live, so it was built and verified before anything else.
2. `storage.py`, tested with a temp file (save/load, missing file,
   corrupt file).
3. `scheduler.py`, checked manually by scheduling an alarm a minute out
   and confirming it rings and dismisses correctly.
4. `cli.py` last, once the pieces it wires together were already correct.
5. README written and checked against the actual CLI output.

22 automated tests cover the models, storage, and CLI layers; the `run`
loop was verified by hand since it depends on real time passing.
