# Design plan

This is the plan worked out before writing code, kept as-is (not rewritten
after the fact) so it reflects the actual reasoning, not a tidied-up
retrospective. `README.md` covers usage; this covers *why* it's built this
way.

## 1. Requirements refinement

The brief was deliberately open: "build an alarm clock as a Python CLI
application," no detailed spec, ~30 minutes. First step was turning that
into a concrete, gradeable scope rather than guessing at hidden
requirements.

**What "alarm clock" has to mean, at minimum**, for the CLI to feel like a
real tool and not a toy:

- You can set an alarm for a specific time.
- The alarm actually goes off at that time while the program is watching.
- You can see what's currently scheduled.
- You can cancel/change your mind.
- The alarm's behavior needs to include one small piece of "clock" logic
  beyond a single fire — a one-shot vs. a recurring alarm — since that's
  the part that actually distinguishes an alarm clock from a `sleep()`
  call plus a `print()`.

**Explicitly out of scope**, and why:

- *A daemon/background service.* Running as a detached process needs
  platform-specific mechanics (launchd/systemd/Task Scheduler) that are a
  separate problem from "alarm clock logic" and would eat the whole time
  budget on plumbing, not on the thing being evaluated.
- *Real audio.* Playing a WAV cross-platform means either a native
  dependency (`playsound`, `simpleaudio`) or OS-specific shell-outs. The
  terminal bell (`\a`) is a deliberate stand-in — it's the same "notify the
  user" responsibility with zero dependency risk. Documented as a known
  trade, not hidden.
- *Timezones, multiple concurrent alarms ringing at once, config files,
  colorized TUI.* Each is a legitimate feature for a real product; none of
  them is what distinguishes a working alarm clock from a broken one at
  this scope.

**Decisions that needed to be made explicitly, because the spec didn't
say:**

| Question | Decision | Why |
|---|---|---|
| CLI style: one-shot commands or an interactive shell? | Subcommands (`add`, `list`, `run`, ...), argparse | Composable, scriptable, testable per-command — an interactive REPL is harder to test and to drive from a screen recording. |
| Where do alarms persist? | Flat JSON file | A handful of alarms doesn't need a database (task explicitly rules that out anyway); JSON is human-inspectable, which matters for a reviewer opening the repo. |
| Does "run" need to be a separate step from "add"? | Yes — `add` just schedules, `run` is the foreground watcher | Mirrors how `cron`/`at` separate "define the job" from "run the scheduler." Makes both halves independently testable: alarm matching logic doesn't need a live clock to test. |
| What happens when an alarm fires? | Beep + blocking dismiss/snooze prompt | An alarm that fires silently into a log isn't an alarm. Blocking is simpler and more predictable than threading input around a poll loop, and this is a single-user foreground CLI, not a multi-alarm real-time system. |

## 2. Architecture

Four small modules, each with one job, so each is testable in isolation
without mocking the others:

```
alarmclock/
  models.py     Alarm dataclass, time/repeat parsing & validation, "is this
                 alarm due right now" logic
  storage.py     Load/save alarms as JSON, atomic writes
  scheduler.py    The run loop: poll the clock, ring due alarms, handle
                 dismiss/snooze
  cli.py         argparse wiring, one function per subcommand
```

`models.py` has no I/O and no clock dependency at runtime — `Alarm.matches(now)`
takes `now` as a parameter rather than calling `datetime.now()` itself, so
every scheduling rule (one-shot fires once, weekday alarms skip weekends,
a disabled alarm never fires) is a pure function test with no sleeping,
no mocking `datetime`, no flakiness.

`storage.py` is the only place that touches the filesystem. Writes go to a
temp file first, then `Path.replace()` (atomic on POSIX and Windows), so a
crash or `Ctrl+C` mid-write can't leave a half-written, corrupt
`alarms.json`.

`scheduler.py` is intentionally thin: load alarms, check the current
minute, ring what's due, sleep a second, repeat. All the "what counts as
due" logic lives in `models.py` so the loop itself stays a few lines and
easy to read against.

`cli.py` has no business logic of its own — each subcommand function loads
via `Store`, calls into `models`/`scheduler`, and prints a result. This
keeps `main()` a pure dispatcher, so CLI tests exercise the same code path
a real terminal invocation would (`main(["add", "07:30"])`), rather than
testing a separate "core" API that the CLI wraps.

## 3. Data model

```
Alarm:
  id: int                    # smallest unused positive int — stable, short
  hour, minute: int
  label: str
  repeat: list[str]          # [] = one-shot; else subset of mon..sun
  enabled: bool
  last_triggered: str|None   # ISO date, guards against firing twice in
                              # the same matching minute
```

`repeat` as a list of weekday abbreviations (rather than an enum of
once/daily/weekly) was chosen so "every Tue/Thu" is representable without
a special case — `daily`/`weekdays`/`weekends` are just convenience
spellings that expand to the same list.

## 4. Implementation plan (order actually followed)

1. **`models.py` first, with its tests.** This is where all the actual
   "alarm clock" logic and edge cases live (time parsing, repeat parsing,
   due-now matching), and it's the highest-risk part to get subtly wrong.
   Building and testing it before any CLI or I/O existed meant the core
   logic was verified independent of everything else.
2. **`storage.py`**, tested with `tmp_path` fixtures — round-trip
   save/load, missing file, corrupt file. Corrupt-file handling
   (`json.JSONDecodeError` → treat as empty) was added here because a
   half-written file is a realistic failure mode given `run` writes on
   every dismiss.
3. **`scheduler.py`**, the thinnest layer, manually smoke-tested end to
   end (scheduled an alarm one minute out, ran `run`, confirmed it rang,
   dismissed it, confirmed it self-disabled in `alarms.json`) rather than
   unit-tested — it's mostly I/O and timing glue over already-tested logic.
4. **`cli.py`** last, once the pieces it orchestrates were already correct,
   tested via `main()` with a temp `--file` per test so tests don't touch
   real user data.
5. **README** written to match what was actually built, not what was
   planned — usage examples were re-run against the real CLI before being
   committed, so the docs don't drift from behavior.

## 5. Testing strategy

- Unit tests for pure logic (`models.py`): valid/invalid time formats,
  repeat-shortcut expansion, id assignment, due-now matching across
  enabled/disabled/repeat/already-fired-today states.
- Integration-style tests for storage (`tmp_path`, real file I/O, no
  mocking) — round trip, missing file, corrupt file.
- CLI tests drive `main()` with an isolated `--file` per test, asserting
  on stdout/stderr and exit codes, covering both the happy path and error
  path (e.g. `add 99:99` → exit 1, stderr message).
- One manual end-to-end run of `run` itself (scheduled an alarm a minute
  out, let it fire, dismissed it, inspected the resulting JSON) — the one
  piece that genuinely depends on wall-clock time and a live terminal, so
  automating it would trade a real check for a fragile one.

22 tests, all passing, runnable with `pytest` from the repo root (see
README for setup).

## 6. Known trade-offs (carried forward, not fixed by scope cut)

- No real audio, no background/daemon mode, no timezone handling — see
  §1 for why these were cut rather than attempted and left half-done.
- `run` blocks on the dismiss/snooze prompt, so two alarms due in the same
  minute ring one after another, not concurrently. Acceptable for a
  single-user foreground tool; would need a different design (non-blocking
  input, or a queue) for anything higher-stakes.
