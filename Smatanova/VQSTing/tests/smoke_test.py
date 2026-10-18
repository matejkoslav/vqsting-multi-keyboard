"""Cross-platform smoke test for VQSTing.

Run from Smatanova/VQSTing:

    python tests/smoke_test.py

It never launches mpv or opens a folder.  The demo database is copied to a
temporary file, so the real instance/database.db is not modified.
"""

import os
import shutil
import sys
import tempfile
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import website
from website import create_app
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


def skip(name, reason):
    print(f"[SKIP] {name} ({reason})")


def make_app():
    db_source = os.path.join(BASE_DIR, "instance", "database.db")
    tmp_db = os.path.join(tempfile.mkdtemp(prefix="vqsting-"), "database.db")
    if os.path.isfile(db_source):
        shutil.copyfile(db_source, tmp_db)
    # Absolute path: sqlite:////tmp/... on POSIX, sqlite:///C:/... on Windows.
    website.DB_NAME = tmp_db.replace(os.sep, "/")
    return create_app()


def main():
    check("platform detected", IS_WINDOWS or sys.platform.startswith("linux"),
          sys.platform)

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
    check("GET /statistics/1 is 200", client.get("/statistics/1").status_code == 200)
    check("GET /admin/ is 200", client.get("/admin/").status_code == 200)

    # --- full participant flow (needs the videos locally) -----------------
    videos_present = os.path.isdir(video_path("ExampleTest", "training"))
    if not videos_present:
        skip("training + test flow", "video/ExampleTest not present")
        return finish()

    client.get("/logout")
    response = client.post("/register", data={
        "username": "smoke_user",
        "password": "smoke_pass",
        "confirm_password": "smoke_pass",
        "role": "1",
    })
    check("participant can register", response.status_code == 302)
    response = client.post("/profile", data={
        "gender": "m",
        "age": "30",
        "glasses": "False",
    })
    check("participant can fill profile", response.status_code == 302)
    response = client.post("/sessions-list", data={
        "session_id": "1",
        "password": "eXamp1e",
    })
    check("participant joins ExampleTest",
          response.status_code == 302 and "/training/1" in response.headers.get("Location", ""))

    check("GET /training/1 is 200", client.get("/training/1").status_code == 200)

    with patch("website.video.play_videos") as player_mock:
        url = "/training_start/1"
        completed = False
        for _ in range(10):
            response = client.get(url)
            if response.status_code == 200:
                completed = True
                break
            location = response.headers.get("Location", "")
            page = client.get(location)
            if page.status_code != 200:
                check("training valuation page is 200", False, location)
                break
            min_value = int(location.rstrip("/").split("/")[-2])
            response = client.post(location, data={"value": str(min_value)})
            if response.status_code == 200:
                completed = True
                break
            url = response.headers.get("Location", "")

        check("training flow completes", completed)
        calls = player_mock.call_args_list
        check("training played mpv with existing files",
              bool(calls) and all(os.path.isfile(p) for c in calls for p in c[0]),
              str(calls[:1]))

    response = client.get("/test/1")
    check("GET /test/1 starts the test", response.status_code == 302)

    with patch("website.video.play_videos") as player_mock:
        url = response.headers.get("Location", "")
        completed = False
        for _ in range(40):
            response = client.get(url)
            if response.status_code == 200:
                completed = True
                break
            location = response.headers.get("Location", "")
            page = client.get(location)
            if page.status_code != 200:
                check("test valuation page is 200", False, location)
                break
            response = client.post(location, data={"value": "3"})
            if response.status_code == 200:
                completed = True
                break
            url = response.headers.get("Location", "")

        check("test flow completes", completed)
        calls = player_mock.call_args_list
        check("test played mpv with existing files",
              bool(calls) and all(os.path.isfile(p) for c in calls for p in c[0]),
              str(calls[:1]))

    return finish()


def finish():
    if failures:
        print(f"\nFAILED: {len(failures)} check(s): {', '.join(failures)}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
