"""Cross-platform smoke test for VQSTing.

Run from Smatanova/VQSTing:

    python tests/smoke_test.py

It never launches mpv or opens a folder.  The demo database is copied to a
temporary file, so the real instance/database.db is not modified.
"""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import website
from website import create_app, keyboards
from website.models import GroupRun, GroupVote, Sequence, Tester, Training, Video
from website.platform_compat import (
    IS_WINDOWS,
    find_mpv,
    open_folder,
    play_videos,
    video_path,
)

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}" + (f" ({detail})" if detail else ""))
        failures.append(name)


def keyboards_checks():
    tmp = tempfile.mkdtemp(prefix="vqsting-keyboards-")
    state_path = os.path.join(tmp, "keyboards.json")
    pid_path = os.path.join(tmp, "listener.pid")
    original = (keyboards.STATE, keyboards.PID)
    keyboards.STATE, keyboards.PID = state_path, pid_path
    try:
        state = keyboards.state()
        check("keyboards: missing files are safe",
              state["listener"] is False and state["devices"] == [] and state["age"] is None,
              str(state))

        with open(state_path, "w") as f:
            f.write("{not json")
        state = keyboards.state()
        check("keyboards: corrupt state is safe",
              state["devices"] == [] and state["age"] is None, str(state))

        if not IS_WINDOWS:
            with open(state_path, "w") as f:
                json.dump({"ts": time.time(), "devices": [{"node": "event3"}]}, f)
            with open(pid_path, "w") as f:
                f.write(str(os.getpid()))
            state = keyboards.state()
            check("keyboards: live listener exposes devices",
                  state["listener"] is True and state["devices"][0]["node"] == "event3",
                  str(state))
            check("keyboards: events and seq are passed through",
                  state["seq"] == 0 and state["events"] == [], str(state))

        with open(state_path, "w") as f:
            json.dump({"ts": time.time(), "seq": 7,
                       "devices": [{"node": "event3"}],
                       "events": [{"seq": 7, "key": "3"}]}, f)
        with open(pid_path, "w") as f:
            f.write("12345")
        with patch("website.keyboards.platform.system", return_value="Windows"), \
                patch("website.keyboards.os.kill") as kill, \
                patch("website.keyboards._alive_windows", return_value=True):
            state = keyboards.state()
        check("keyboards: Windows never uses os.kill", kill.called is False, str(state))
        check("keyboards: Windows is supported and exposes devices",
              state["supported"] is True and state["listener"] is True
              and state["devices"][0]["node"] == "event3"
              and state["seq"] == 7 and state["events"][0]["key"] == "3", str(state))
    finally:
        keyboards.STATE, keyboards.PID = original


def listener_checks():
    import pwd
    from tools import keyboard_listener

    uid = os.getuid()
    gid = pwd.getpwuid(uid).pw_gid
    calls = []
    def record(name):
        def recorder(*args):
            calls.append((name, args))
        return recorder

    with patch.object(keyboard_listener.os, "chown", record("chown")), \
            patch.object(keyboard_listener.os, "setgroups", record("setgroups")), \
            patch.object(keyboard_listener.os, "setgid", record("setgid")), \
            patch.object(keyboard_listener.os, "setuid", record("setuid")):
        keyboard_listener._drop_privileges(uid)

    names = [name for name, _ in calls]
    check("listener: chowns run dir and socket",
          ("chown", (keyboard_listener.RUN_DIR, uid, gid)) in calls
          and ("chown", (keyboard_listener.OPEN_SOCK, uid, gid)) in calls,
          str(calls))
    check("listener: drops supplementary groups",
          ("setgroups", ([],)) in calls, str(calls))
    check("listener: drops groups before switching user",
          "setgroups" in names and "setgid" in names and "setuid" in names
          and names.index("setgroups") < names.index("setgid") < names.index("setuid"),
          str(names))

    state_path = os.path.join(tempfile.mkdtemp(prefix="vqsting-listener-"), "keyboards.json")
    saved = (dict(keyboard_listener.devices), keyboard_listener.seq,
             list(keyboard_listener.events), keyboard_listener.STATE)
    try:
        keyboard_listener.STATE = state_path
        keyboard_listener.devices.clear()
        keyboard_listener.devices["event3"] = {
            "id": "linux:abc", "node": "event3", "name": "Test keyboard",
            "uniq": "abc", "phys": "", "key": None, "at": None, "seq": None,
        }
        keyboard_listener.seq = 0
        keyboard_listener.events.clear()

        for key in ("1", "2", "3"):
            keyboard_listener.record_key("event3", key)

        check("listener: seq counts every key-down", keyboard_listener.seq == 3,
              str(keyboard_listener.seq))
        device = keyboard_listener.devices["event3"]
        check("listener: device remembers its last event",
              device["key"] == "3" and device["seq"] == 3, str(device))
        check("listener: events carry device id, seq and key",
              [e["key"] for e in keyboard_listener.events] == ["1", "2", "3"]
              and all(e["device_id"] == "linux:abc" for e in keyboard_listener.events),
              str(list(keyboard_listener.events)))

        keyboard_listener._write()
        with open(state_path) as f:
            written = json.load(f)
        check("listener: state file follows the JSON contract",
              written["platform"] == "linux" and written["seq"] == 3
              and written["devices"][0]["id"] == "linux:abc"
              and written["events"][-1]["key"] == "3", str(written))

        for _ in range(70):
            keyboard_listener.record_key("event3", "1")
        events = list(keyboard_listener.events)
        check("listener: events keep only the last 64",
              len(events) == 64 and events[0]["seq"] == 10 and events[-1]["seq"] == 73,
              f"{len(events)} events, {events[0]['seq']}..{events[-1]['seq']}")
    finally:
        devices, seq, events, state = saved
        keyboard_listener.devices.clear()
        keyboard_listener.devices.update(devices)
        keyboard_listener.seq = seq
        keyboard_listener.events.clear()
        keyboard_listener.events.extend(events)
        keyboard_listener.STATE = state


def listener_lifecycle_checks():
    """pid file must never outlive its listener, and never kill a stranger."""
    import tempfile
    from tools import keyboard_listener

    tmp = tempfile.mkdtemp(prefix="vqsting-pid-")
    pid_path = os.path.join(tmp, "listener.pid")
    original = keyboard_listener.PID
    keyboard_listener.PID = pid_path
    try:
        with open(pid_path, "w") as f:
            f.write(str(os.getpid()))
        keyboard_listener._cleanup()
        check("listener: cleanup removes its own pid file",
              not os.path.exists(pid_path))

        with open(pid_path, "w") as f:
            f.write("424242")
        keyboard_listener._cleanup()
        check("listener: cleanup keeps a pid file of another process",
              os.path.exists(pid_path))
        os.unlink(pid_path)

        keyboard_listener._cleanup()
        check("listener: cleanup without a pid file is safe", True)

        with open(pid_path, "w") as f:
            f.write(str(os.getpid()))
        check("listener: a live non-listener pid is not 'already running'",
              keyboard_listener._already_running() is None)

        with patch("tools.keyboard_listener.os.kill",
                   side_effect=ProcessLookupError):
            check("listener: a stale pid is not 'already running'",
                  keyboard_listener._already_running() is None)
    finally:
        keyboard_listener.PID = original
        shutil.rmtree(tmp, ignore_errors=True)


def windows_listener_checks():
    script = os.path.join(BASE_DIR, "tools", "windows_keyboard_listener.py")
    # PYTHONIOENCODING=ascii imitates the cp1252 console on Windows: any
    # non-ASCII print would crash the listener before it can exit 0.
    env = dict(os.environ, PYTHONIOENCODING="ascii")
    result = subprocess.run([sys.executable, script, "--selftest"],
                            capture_output=True, text=True, env=env)
    check("windows listener: --selftest exits 0 on a plain console",
          result.returncode == 0, (result.stdout + result.stderr).strip())


def make_app():
    db_source = os.path.join(BASE_DIR, "instance", "database.db")
    tmp_db = os.path.join(tempfile.mkdtemp(prefix="vqsting-"), "database.db")
    if os.path.isfile(db_source):
        shutil.copyfile(db_source, tmp_db)
    # Absolute path: sqlite:////tmp/... on POSIX, sqlite:///C:/... on Windows.
    website.DB_NAME = tmp_db.replace(os.sep, "/")
    app = create_app()
    # The copy may come from a working tree that has a real group run in it;
    # start every test run from a clean group state.
    with app.app_context():
        GroupVote.query.delete()
        Tester.query.delete()
        GroupRun.query.delete()
        website.db.session.commit()
    return app


class FakeListener:
    """Writes the same state file as tools/keyboard_listener.py, without devices."""

    def __init__(self, state_path, pid_path):
        self.state_path = state_path
        self.devices = [
            {"id": "linux:kbd1", "name": "Keyboard 1", "node": "event3",
             "uniq": "kbd1", "phys": "", "key": None, "at": None, "seq": None},
            {"id": "linux:kbd2", "name": "Keyboard 2", "node": "event18",
             "uniq": "kbd2", "phys": "", "key": None, "at": None, "seq": None},
        ]
        self.events = []
        self.seq = 0
        with open(pid_path, "w") as f:
            f.write(str(os.getpid()))
        self.write()

    def press(self, device_id, key):
        self.seq += 1
        now = time.time()
        for device in self.devices:
            if device["id"] == device_id:
                device["key"] = key
                device["at"] = now
                device["seq"] = self.seq
        self.events.append({"seq": self.seq, "at": now,
                            "device_id": device_id, "key": key})
        self.events = self.events[-64:]
        self.write()

    def write(self):
        with open(self.state_path, "w") as f:
            json.dump({"ts": time.time(), "platform": "linux", "seq": self.seq,
                       "devices": self.devices, "events": self.events}, f)


def make_fake_videos(app):
    """Create an empty video/ tree; the files are only checked for existence."""
    root = tempfile.mkdtemp(prefix="vqsting-video-")
    with app.app_context():
        files = []
        for sequence in Sequence.query.filter_by(id_session=1).all():
            for video in Video.query.filter_by(id_sequence=sequence.id).all():
                files.append(("ref_seq" if video.reference else "test_seq", video.name))
        for training in Training.query.filter_by(id_session=1).all():
            files.append(("training", training.name))

    for folder, name in files:
        folder_path = os.path.join(root, "video", "ExampleTest", folder)
        os.makedirs(folder_path, exist_ok=True)
        open(os.path.join(folder_path, name), "w").close()
    open(os.path.join(root, "video", "grey50.mp4"), "w").close()
    return root


def group_checks():
    app = make_app()
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin"})

    video_root = make_fake_videos(app)
    listener_dir = tempfile.mkdtemp(prefix="vqsting-group-")
    state_path = os.path.join(listener_dir, "keyboards.json")
    pid_path = os.path.join(listener_dir, "listener.pid")
    original_paths = (keyboards.STATE, keyboards.PID)
    original_cwd = os.getcwd()
    keyboards.STATE, keyboards.PID = state_path, pid_path
    listener = FakeListener(state_path, pid_path)
    os.chdir(video_root)
    try:
        response = client.get("/group/1")
        check("group: setup page is 200", response.status_code == 200)

        response = client.post("/group/1/add", json={})
        check("group: first tester is added",
              response.status_code == 200 and response.get_json()["seat"] == 1,
              response.get_data(as_text=True))
        response = client.post("/group/1/add", json={})
        check("group: second tester is added",
              response.status_code == 200 and response.get_json()["seat"] == 2,
              response.get_data(as_text=True))

        client.post("/group/1/pair", json={"seat": 1})
        listener.press("linux:kbd1", "Enter")
        state = client.get("/group/1/state?since=0").get_json()
        check("group: pairing binds the next free keyboard",
              state["testers"][0]["keyboard_id"] == "linux:kbd1"
              and state["testers"][0]["keyboard_name"] == "Keyboard 1"
              and state["pairing_seat"] is None, str(state["testers"]))

        client.post("/group/1/pair", json={"seat": 2})
        listener.press("linux:kbd2", "Enter")
        state = client.get("/group/1/state?since=0").get_json()
        check("group: both testers have their own keyboard",
              [t["keyboard_id"] for t in state["testers"]] == ["linux:kbd1", "linux:kbd2"],
              str(state["testers"]))

        client.post("/group/1/tester", json={"seat": 1, "age": 23, "glasses": True})
        client.post("/group/1/tester", json={"seat": 2, "age": 31, "glasses": False})
        state = client.get("/group/1/state?since=0").get_json()
        check("group: demographics are stored",
              [(t["age"], t["glasses"]) for t in state["testers"]] == [(23, True), (31, False)],
              str(state["testers"]))
        check("group: state follows the JSON contract",
              set(state) == {"phase", "listener", "park", "scale", "testers",
                             "events", "pairing_seat"}
              and set(state["park"]) == {"id", "current", "total", "seconds_left",
                                         "round_open"}
              and set(state["scale"]) == {"method", "labels"}
              and set(state["testers"][0]) == {"seat", "keyboard_id", "keyboard_name",
                                               "age", "glasses", "gender", "vote",
                                               "last_seq"}
              and state["scale"]["labels"] == ["IMPERCEPTIBLE",
                                               "PERCEPTIBLE BUT NOT ANNOYING",
                                               "SLIGHTLY ANNOYING", "ANNOYING",
                                               "VERY ANNOYING"],
              str(state))

        with patch("website.group.play_videos") as player:
            response = client.post("/group/1/start")
            check("group: start redirects to the first round",
                  response.status_code == 302
                  and "/group/1/play" in response.headers.get("Location", ""))
            state = client.get("/group/1/state?since=0").get_json()
            check("group: start builds the shared video order",
                  state["phase"] == "running" and state["park"]["total"] == 12,
                  str(state["park"]))

            for round_number in (1, 2, 3):
                response = client.get("/group/1/play")
                check(f"group: round {round_number} voting page is 200",
                      response.status_code == 200, str(response.status_code))
                state = client.get("/group/1/state?since=0").get_json()
                check(f"group: round {round_number} stays open for 9 seconds",
                      state["park"]["round_open"] is True
                      and 8.0 < state["park"]["seconds_left"] <= 9.0,
                      str(state["park"]))

                if round_number == 1:
                    listener.press("linux:kbd1", "4")
                    listener.press("linux:kbd2", "2")
                    state = client.get("/group/1/state?since=0").get_json()
                    check("group: keyboard votes reach both testers",
                          [t["vote"] for t in state["testers"]] == [4, 2],
                          str(state["testers"]))
                elif round_number == 2:
                    listener.press("linux:kbd1", "3")
                    response = client.post("/group/1/vote", json={"seat": 2, "value": 5})
                    check("group: mouse vote is accepted", response.status_code == 200,
                          response.get_data(as_text=True))
                    state = client.get("/group/1/state?since=0").get_json()
                    check("group: keyboard and mouse votes mix",
                          [t["vote"] for t in state["testers"]] == [3, 5],
                          str(state["testers"]))
                else:
                    client.post("/group/1/vote", json={"seat": 1, "value": 5})
                    client.post("/group/1/vote", json={"seat": 2, "value": 1})
                    state = client.get("/group/1/state?since=0").get_json()
                    check("group: mouse votes close the round",
                          [t["vote"] for t in state["testers"]] == [5, 1]
                          and state["park"]["round_open"] is False,
                          str(state))

                response = client.post("/group/1/next")
                check(f"group: round {round_number} advances",
                      response.status_code == 302
                      and "/group/1/play" in response.headers.get("Location", ""))

            check("group: every round played the existing video files",
                  player.call_count == 3
                  and all(os.path.isfile(path) for call in player.call_args_list
                          for path in call.args),
                  str(player.call_args_list))

        with patch("website.group.play_videos") as training_player:
            response = client.post("/group/1/training")
        check("group: training plays one playlist for everyone",
              response.status_code == 302 and training_player.call_count == 1
              and len(training_player.call_args.args) == 9,
              str(training_player.call_args))

        with app.app_context():
            run = GroupRun.query.filter_by(id_session=1).first()
            total = len(run.order.split(","))
            run.current_id = total - 1
            website.db.session.commit()

        response = client.post("/group/1/next")
        check("group: the last round goes to results",
              response.status_code == 302
              and "/group/1/results" in response.headers.get("Location", ""))

        response = client.get("/group/1/results")
        check("group: results page is 200", response.status_code == 200)
        check("group: results show testers and unfinished rounds",
              b"Tester 1" in response.data and b"Tester 2" in response.data
              and b"n/a" in response.data)

        with patch("website.group.open_folder") as folder:
            response = client.get("/group/1/export")
        check("group: export redirects back to results",
              response.status_code == 302
              and "/group/1/results" in response.headers.get("Location", ""))
        check("group: export opens the csv folder", folder.called)

        csv_path = os.path.join(video_root, "csv", "ExampleTest.csv")
        check("group: export writes csv/<session>.csv", os.path.isfile(csv_path), csv_path)
        if os.path.isfile(csv_path):
            with open(csv_path, newline="") as handle:
                rows = list(csv.reader(handle))
            check("group: csv keeps the legacy header",
                  rows[0] == ["ExampleTest"]
                  and rows[1] == ["dcr", "Samsung U24E590D UHD"]
                  and rows[2] == [], str(rows[:3]))
            check("group: csv has testers as columns",
                  rows[3] == ["", "Tester 1", "Tester 2"]
                  and rows[4] == ["", "23", "31"]
                  and rows[5] == ["", "ano", "nie"], str(rows[3:6]))
            data_rows = rows[6:]
            numeric = [cell for row in data_rows for cell in row[1:] if cell != "n/a"]
            check("group: csv has one row per tested video", len(data_rows) == 12,
                  str(len(data_rows)))
            check("group: csv uses n/a for rounds without a vote",
                  len(numeric) == 6 and all(cell in {"1", "2", "3", "4", "5"}
                                            for cell in numeric), str(numeric))

        response = client.get("/keyboards")
        check("GET /keyboards is 200", response.status_code == 200)
        response = client.get("/keyboards/state")
        state = response.get_json()
        check("GET /keyboards/state exposes the live listener",
              response.status_code == 200 and state["listener"] is True
              and state["seq"] >= 5
              and [event["key"] for event in state["events"]][:2] == ["Enter", "Enter"],
              str(state))

        response = client.post("/group/1/reset")
        check("group: reset redirects to setup",
              response.status_code == 302
              and "/group/1" in response.headers.get("Location", ""))
        check("group: setup page works after reset", client.get("/group/1").status_code == 200)
        with app.app_context():
            run = GroupRun.query.filter_by(id_session=1).first()
            check("group: reset starts a fresh run",
                  run is not None and run.phase == "setup")
            check("group: reset removes testers and votes",
                  Tester.query.filter_by(id_group_run=run.id).count() == 0
                  and GroupVote.query.count() == 0)

        seats = [client.post("/group/1/add", json={}).get_json()["seat"] for _ in range(4)]
        check("group: four testers fit side by side", seats == [1, 2, 3, 4], str(seats))
        response = client.post("/group/1/add", json={})
        check("group: a fifth tester is refused", response.status_code == 400,
              str(response.status_code))

        listener.press("linux:kbd3", "Enter")   # pressed before pairing is armed
        client.post("/group/1/pair", json={"seat": 1})
        state = client.get("/group/1/state").get_json()
        check("group: only a key pressed after arming pairs a keyboard",
              state["testers"][0]["keyboard_id"] is None and state["pairing_seat"] == 1,
              str(state["testers"][0]))
        listener.press("linux:kbd1", "Enter")
        state = client.get("/group/1/state").get_json()
        check("group: a key pressed after arming pairs the keyboard",
              state["testers"][0]["keyboard_id"] == "linux:kbd1",
              str(state["testers"][0]))

        response = client.post("/group/1/start")
        check("group: start needs an age for every tester",
              response.status_code == 302
              and "/group/1" in response.headers.get("Location", ""),
              str(response.status_code))

        # a second run must not inherit the votes of the first one
        client.post("/group/1/reset")
        client.post("/group/1/add", json={})
        client.post("/group/1/add", json={})
        client.post("/group/1/tester", json={"seat": 1, "age": 23})
        client.post("/group/1/tester", json={"seat": 2, "age": 31})
        for seat, keyboard in ((1, "linux:kbd1"), (2, "linux:kbd2")):
            client.post("/group/1/pair", json={"seat": seat})
            listener.press(keyboard, "Enter")
            client.get("/group/1/state")
        with patch("website.group.play_videos"):
            client.post("/group/1/start")
            client.get("/group/1/play")
        listener.press("linux:kbd1", "4")
        listener.press("linux:kbd2", "2")
        client.get("/group/1/state")
        with app.app_context():
            run = GroupRun.query.filter_by(id_session=1).first()
            before = GroupVote.query.filter_by(id_group_run=run.id).count()
        with patch("website.group.play_videos"):
            client.post("/group/1/start")
        with app.app_context():
            run = GroupRun.query.filter_by(id_session=1).first()
            after = GroupVote.query.filter_by(id_group_run=run.id).count()
        check("group: a second start clears the votes of the first run",
              before == 2 and after == 0, f"{before} -> {after}")

        # a tester who misses a round must not inherit the previous round's vote
        client.post("/group/1/reset")
        client.post("/group/1/add", json={})
        client.post("/group/1/add", json={})
        client.post("/group/1/tester", json={"seat": 1, "age": 23})
        client.post("/group/1/tester", json={"seat": 2, "age": 31})
        for seat, keyboard in ((1, "linux:kbd1"), (2, "linux:kbd2")):
            client.post("/group/1/pair", json={"seat": seat})
            listener.press(keyboard, "Enter")
            client.get("/group/1/state")
        with patch("website.group.play_videos"):
            client.post("/group/1/start")
            client.get("/group/1/play")
        listener.press("linux:kbd1", "4")
        listener.press("linux:kbd2", "3")
        client.get("/group/1/state")
        with patch("website.group.play_videos"):
            client.post("/group/1/next")
            client.get("/group/1/play")
        client.post("/group/1/vote", json={"seat": 1, "value": 5})
        with app.app_context():
            run = GroupRun.query.filter_by(id_session=1).first()
            run.round_started = time.time() - 30    # let the round time out
            website.db.session.commit()
        state = client.get("/group/1/state").get_json()
        check("group: a missed round does not reuse the previous vote",
              [t["vote"] for t in state["testers"]] == [5, None]
              and state["park"]["round_open"] is False,
              str(state["testers"]))
        client.post("/group/1/reset")
    finally:
        os.chdir(original_cwd)
        keyboards.STATE, keyboards.PID = original_paths


def main():
    check("platform detected", IS_WINDOWS or sys.platform.startswith("linux"),
          sys.platform)

    keyboards_checks()
    if not IS_WINDOWS:
        listener_lifecycle_checks()
    if not IS_WINDOWS:
        listener_checks()
    windows_listener_checks()

    # --- platform helpers -------------------------------------------------
    expected = "video" + os.sep + "ExampleTest" + os.sep + "test_seq"
    check("video_path uses native separators", video_path("ExampleTest", "test_seq") == expected,
          video_path("ExampleTest", "test_seq"))

    player = find_mpv()
    check("find_mpv returns a command", bool(player), player)

    with patch("website.platform_compat.subprocess.call") as mocked:
        play_videos("a.mp4", "b.mp4")
        args = mocked.call_args[0][0]
        check("play_videos builds mpv command",
              player in args and "--fs" in args and args[-2:] == ["a.mp4", "b.mp4"],
              str(args))

    with patch("website.platform_compat.subprocess.call") as mocked:
        open_folder("csv")
        args, kwargs = mocked.call_args
        if IS_WINDOWS:
            check("open_folder uses start on Windows",
                  args[0] == ["start", "csv"] and kwargs.get("shell") is True,
                  str(args))
        else:
            check("open_folder uses xdg-open on Linux/macOS",
                  args[0][1:] == ["csv"] and args[0][0] in ("xdg-open", "open"),
                  str(args))

    # --- app boot ---------------------------------------------------------
    app = make_app()
    client = app.test_client()

    check("GET / is 200", client.get("/").status_code == 200)
    check("GET /login is 200", client.get("/login").status_code == 200)

    response = client.post("/login", data={"username": "admin", "password": "admin"},
                           follow_redirects=True)
    check("admin can log in", b"My test sessions" in response.data)

    check("GET /my-table-sessions is 200",
          client.get("/my-table-sessions").status_code == 200)
    check("GET /details/1 is 200", client.get("/details/1").status_code == 200)
    check("GET /group/1 is 200", client.get("/group/1").status_code == 200)
    check("GET /keyboards is 200", client.get("/keyboards").status_code == 200)
    check("GET /admin/table-users is 200",
          client.get("/admin/table-users").status_code == 200)

    state = client.get("/keyboards/state")
    check("GET /keyboards/state is JSON",
          state.status_code == 200 and "listener" in state.get_json(),
          state.get_data(as_text=True))

    response = client.get("/statistics/1")
    check("GET /statistics/1 redirects to group results",
          response.status_code == 302
          and "/group/1/results" in response.headers.get("Location", ""),
          str(response.status_code))
    response = client.get("/admin/")
    check("GET /admin/ redirects to the user table",
          response.status_code == 302
          and "/admin/table-users" in response.headers.get("Location", ""),
          str(response.status_code))

    group_checks()

    return finish()


def finish():
    if failures:
        print(f"\nFAILED: {len(failures)} check(s): {', '.join(failures)}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
