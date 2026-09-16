from datetime import datetime

import pytest

from alarmclock.models import Alarm, InvalidAlarmError, parse_repeat, parse_time


def test_parse_time_valid():
    t = parse_time("07:05")
    assert (t.hour, t.minute) == (7, 5)


@pytest.mark.parametrize("value", ["25:00", "7:5", "abc", "24:00", "12:60"])
def test_parse_time_invalid(value):
    with pytest.raises(InvalidAlarmError):
        parse_time(value)


def test_parse_repeat_shortcuts():
    assert parse_repeat("once") == []
    assert parse_repeat(None) == []
    assert parse_repeat("daily") == ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    assert parse_repeat("weekdays") == ["mon", "tue", "wed", "thu", "fri"]
    assert parse_repeat("weekends") == ["sat", "sun"]


def test_parse_repeat_custom_days_deduped_and_ordered():
    assert parse_repeat("wed,mon,mon") == ["mon", "wed"]


def test_parse_repeat_rejects_unknown_day():
    with pytest.raises(InvalidAlarmError):
        parse_repeat("funday")


def test_new_alarm_assigns_next_free_id():
    existing = [Alarm(id=1, hour=7, minute=0), Alarm(id=3, hour=8, minute=0)]
    alarm = Alarm.new("09:00", existing=existing)
    assert alarm.id == 2


def test_matches_one_shot_fires_once_per_day():
    alarm = Alarm(id=1, hour=7, minute=30)
    now = datetime(2026, 1, 1, 7, 30)
    assert alarm.matches(now)
    alarm.last_triggered = now.date().isoformat()
    assert not alarm.matches(now)


def test_matches_respects_repeat_days():
    # 2026-01-05 is a Monday
    alarm = Alarm(id=1, hour=6, minute=0, repeat=["tue", "thu"])
    monday = datetime(2026, 1, 5, 6, 0)
    tuesday = datetime(2026, 1, 6, 6, 0)
    assert not alarm.matches(monday)
    assert alarm.matches(tuesday)


def test_matches_ignores_disabled_alarm():
    alarm = Alarm(id=1, hour=7, minute=0, enabled=False)
    assert not alarm.matches(datetime(2026, 1, 1, 7, 0))


def test_matches_wrong_time_does_not_fire():
    alarm = Alarm(id=1, hour=7, minute=0)
    assert not alarm.matches(datetime(2026, 1, 1, 7, 1))
