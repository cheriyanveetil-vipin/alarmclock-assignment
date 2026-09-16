# alarmclock

A terminal alarm clock. Set alarms, list them, and run a foreground watcher
that beeps and prints an alert when one is due.

## Requirements

Python 3.9+, standard library only — no dependencies to install.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
```

This installs an `alarmclock` command inside the venv. Alternatively, skip
the install and run it directly with `python -m alarmclock` (still inside
the activated venv, or with any Python 3.9+ interpreter — it has no
third-party dependencies).

## Usage

```bash
# add an alarm
alarmclock add 07:30 -l "wake up" -r weekdays

# repeat options: once (default) | daily | weekdays | weekends | mon,wed,fri
alarmclock add 22:00 -l "wind down" -r daily

# list alarms
alarmclock list

# disable / enable / remove by id
alarmclock disable 1
alarmclock enable 1
alarmclock remove 1

# remove everything
alarmclock clear

# start the watcher (foreground, Ctrl+C to stop)
alarmclock run
```

When an alarm fires, `run` beeps and prompts:

```
⏰ ALARM 07:30 - wake up
Press Enter to dismiss, or 's' + Enter to snooze 5 min:
```

One-shot alarms (`once`) disable themselves after firing. Repeating alarms
re-arm automatically for their next scheduled day.

Alarms persist to `~/.alarmclock/alarms.json` (override with `--file PATH` or
the `ALARMCLOCK_HOME` env var — useful for tests or running multiple
independent alarm sets).

## Tests

```bash
source .venv/bin/activate
pip install pytest
pytest
```

## Design notes

- **Storage**: alarms are plain JSON on disk, written atomically (write to a
  temp file, then rename) so a crash mid-write can't corrupt the file. No
  database — a handful of alarms doesn't need one.
- **Scheduling**: `run` polls once a second and compares the current
  `HH:MM` (and weekday, for repeating alarms) against stored alarms. A
  `last_triggered` date stamp on each alarm prevents it firing twice inside
  the same matching minute.
- **Ringing is synchronous**: when an alarm fires, the watcher blocks on the
  dismiss/snooze prompt before resuming the poll loop. This is a deliberate
  simplification — a real alarm clock rarely has two alarms firing in the
  same minute, and a blocking prompt is far simpler and more testable than
  threading input handling around the poll loop.
- **IDs**: alarms get the smallest unused positive integer, so ids stay
  short and stable across removals instead of growing forever.
- **No web UI, no database, single dependency-free package** per the
  exercise's constraints.

## What I'd add next with more time

- Real audio playback (a WAV via a cross-platform sound library) instead of
  the terminal bell.
- A background/daemon mode (e.g. via `launchd`/`systemd` or a detached
  process) instead of requiring a foreground terminal.
- Time zone awareness for alarms set while traveling.
