from alarmclock.cli import main


def test_add_and_list(tmp_path, capsys):
    file = str(tmp_path / "alarms.json")
    assert main(["--file", file, "add", "07:30", "-l", "wake up", "-r", "weekdays"]) == 0
    capsys.readouterr()

    assert main(["--file", file, "list"]) == 0
    out = capsys.readouterr().out
    assert "07:30" in out
    assert "wake up" in out
    assert "weekdays" in out


def test_add_rejects_bad_time(tmp_path, capsys):
    file = str(tmp_path / "alarms.json")
    assert main(["--file", file, "add", "99:99"]) == 1
    err = capsys.readouterr().err
    assert "Invalid time" in err


def test_remove(tmp_path, capsys):
    file = str(tmp_path / "alarms.json")
    main(["--file", file, "add", "07:30"])
    capsys.readouterr()

    assert main(["--file", file, "remove", "1"]) == 0
    assert main(["--file", file, "remove", "1"]) == 1  # already gone

    main(["--file", file, "list"])
    out = capsys.readouterr().out
    assert "No alarms set." in out


def test_disable_and_enable(tmp_path, capsys):
    file = str(tmp_path / "alarms.json")
    main(["--file", file, "add", "07:30"])
    capsys.readouterr()

    assert main(["--file", file, "disable", "1"]) == 0
    main(["--file", file, "list"])
    assert "[off]" in capsys.readouterr().out

    assert main(["--file", file, "enable", "1"]) == 0
    main(["--file", file, "list"])
    assert "[on]" in capsys.readouterr().out


def test_clear(tmp_path, capsys):
    file = str(tmp_path / "alarms.json")
    main(["--file", file, "add", "07:30"])
    main(["--file", file, "add", "08:00"])
    capsys.readouterr()

    assert main(["--file", file, "clear"]) == 0
    main(["--file", file, "list"])
    assert "No alarms set." in capsys.readouterr().out
