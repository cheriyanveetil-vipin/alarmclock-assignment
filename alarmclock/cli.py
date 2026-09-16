"""Argument parsing and subcommand dispatch."""

from __future__ import annotations

import argparse
import sys

from .models import Alarm, InvalidAlarmError
from .scheduler import run as run_loop
from .storage import Store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarmclock",
        description="A simple terminal alarm clock.",
    )
    parser.add_argument(
        "--file", dest="file", default=None,
        help="path to the alarms JSON file (default: ~/.alarmclock/alarms.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new alarm")
    p_add.add_argument("time", help="24h time, e.g. 07:30")
    p_add.add_argument("-l", "--label", default="", help="optional label")
    p_add.add_argument(
        "-r", "--repeat", default="once",
        help="once|daily|weekdays|weekends|mon,wed,fri (default: once)",
    )

    sub.add_parser("list", help="list all alarms")

    p_rm = sub.add_parser("remove", help="remove an alarm by id")
    p_rm.add_argument("id", type=int)

    p_toggle = sub.add_parser("enable", help="enable an alarm by id")
    p_toggle.add_argument("id", type=int)

    p_disable = sub.add_parser("disable", help="disable an alarm by id")
    p_disable.add_argument("id", type=int)

    sub.add_parser("clear", help="remove all alarms")

    sub.add_parser("run", help="start watching the clock and ring due alarms")

    return parser


def cmd_add(args, store: Store) -> int:
    alarms = store.load()
    try:
        alarm = Alarm.new(args.time, label=args.label, repeat_value=args.repeat, existing=alarms)
    except InvalidAlarmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    alarms.append(alarm)
    store.save(alarms)
    print(f"Added alarm #{alarm.id} at {alarm.time_str} ({alarm.repeat_str})")
    return 0


def cmd_list(args, store: Store) -> int:
    alarms = sorted(store.load(), key=lambda a: (a.hour, a.minute))
    if not alarms:
        print("No alarms set.")
        return 0
    for a in alarms:
        status = "on" if a.enabled else "off"
        label = f" - {a.label}" if a.label else ""
        print(f"#{a.id:<3} {a.time_str}  [{a.repeat_str:<8}] [{status}]{label}")
    return 0


def cmd_remove(args, store: Store) -> int:
    alarms = store.load()
    remaining = [a for a in alarms if a.id != args.id]
    if len(remaining) == len(alarms):
        print(f"No alarm with id {args.id}", file=sys.stderr)
        return 1
    store.save(remaining)
    print(f"Removed alarm #{args.id}")
    return 0


def _set_enabled(args, store: Store, enabled: bool) -> int:
    alarms = store.load()
    for a in alarms:
        if a.id == args.id:
            a.enabled = enabled
            store.save(alarms)
            print(f"Alarm #{args.id} {'enabled' if enabled else 'disabled'}")
            return 0
    print(f"No alarm with id {args.id}", file=sys.stderr)
    return 1


def cmd_enable(args, store: Store) -> int:
    return _set_enabled(args, store, True)


def cmd_disable(args, store: Store) -> int:
    return _set_enabled(args, store, False)


def cmd_clear(args, store: Store) -> int:
    store.save([])
    print("All alarms removed.")
    return 0


def cmd_run(args, store: Store) -> int:
    run_loop(store)
    return 0


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "remove": cmd_remove,
    "enable": cmd_enable,
    "disable": cmd_disable,
    "clear": cmd_clear,
    "run": cmd_run,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store(args.file)
    handler = COMMANDS[args.command]
    return handler(args, store)


if __name__ == "__main__":
    sys.exit(main())
