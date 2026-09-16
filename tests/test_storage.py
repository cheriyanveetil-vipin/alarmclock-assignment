from alarmclock.models import Alarm
from alarmclock.storage import Store


def test_save_and_load_round_trip(tmp_path):
    store = Store(tmp_path / "alarms.json")
    alarms = [
        Alarm(id=1, hour=7, minute=0, label="wake up", repeat=["mon", "tue"]),
        Alarm(id=2, hour=8, minute=15, enabled=False),
    ]
    store.save(alarms)

    loaded = store.load()
    assert [a.to_dict() for a in loaded] == [a.to_dict() for a in alarms]


def test_load_missing_file_returns_empty_list(tmp_path):
    store = Store(tmp_path / "does-not-exist.json")
    assert store.load() == []


def test_load_corrupt_file_returns_empty_list(tmp_path):
    path = tmp_path / "alarms.json"
    path.write_text("not json")
    store = Store(path)
    assert store.load() == []
