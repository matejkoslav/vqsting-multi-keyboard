"""Group mode: N testers on one PC, one shared monitor, one keyboard each.

The tester's physical keyboard is their identity; the listener state is read
only through ``website.keyboards.state()`` and never from the JSON file.
"""

import os
import random
import time

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from . import db, keyboards, role_required
from . import export as export_files
from .models import (GroupRun, GroupVote, Sequence, Session, Tester, Training,
                     Video)
from .platform_compat import open_folder, play_videos, video_path

group = Blueprint('group', __name__)

ROUND_SECONDS = 9
MAX_TESTERS = 4

ACR_SCALE = ["EXCELLENT", "GOOD", "FAIR", "POOR", "BAD"]
DCR_SCALE = ["IMPERCEPTIBLE", "PERCEPTIBLE BUT NOT ANNOYING",
             "SLIGHTLY ANNOYING", "ANNOYING", "VERY ANNOYING"]

VOTE_KEYS = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}


# ---------- small helpers -------------------------------------------------

def _owned_session(id_session):
    session = Session.query.filter_by(id=id_session).first()
    if session is None or session.id_user != current_user.id:
        return None
    return session


def _run_for(session):
    """The single group run of a session; created on the first setup visit."""
    run = GroupRun.query.filter_by(id_session=session.id).first()
    if run is None:
        run = GroupRun(id_session=session.id, order="", current_id=0,
                       phase="setup")
        db.session.add(run)
        db.session.commit()
    return run


def _testers(run):
    return Tester.query.filter_by(id_group_run=run.id).order_by(Tester.seat).all()


def _tester(run, seat):
    return Tester.query.filter_by(id_group_run=run.id, seat=seat).first()


def _ensure_tester(run, seat):
    tester = _tester(run, seat)
    if tester is None:
        tester = Tester(id_group_run=run.id, seat=seat, last_seq=0)
        db.session.add(tester)
        db.session.commit()
    return tester


def _order_ids(run):
    if not run.order:
        return []
    return [int(item.strip()) for item in run.order.split(",") if item.strip()]


def _current_video(run):
    order = _order_ids(run)
    if 0 <= run.current_id < len(order):
        return Video.query.filter_by(id=order[run.current_id]).first()
    return None


def _scale(session):
    if session.test_method == "dcr":
        return "dcr", DCR_SCALE
    return "acr", ACR_SCALE


def _parse_int(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "ano", "on"):
        return True
    if text in ("0", "false", "no", "nie", "off"):
        return False
    return None


def _glasses_label(tester):
    if tester.glasses is None:
        return "n/a"
    return "ano" if tester.glasses else "nie"


def _tester_label(tester):
    """The tester's name, or "Tester N" while no name is entered."""
    return tester.name or f"Tester {tester.seat}"


def _clean_name(value):
    text = " ".join(str(value or "").split())
    return text[:100] or None


def _payload():
    return request.get_json(silent=True) or request.form


# ---------- votes and rounds ---------------------------------------------

def _votes_of_video(run, video):
    return GroupVote.query.filter_by(id_group_run=run.id, id_video=video.id).all()


def _store_vote(run, tester, video, value):
    vote = GroupVote.query.filter_by(id_tester=tester.id, id_video=video.id).first()
    if vote is None:
        vote = GroupVote(id_group_run=run.id, id_tester=tester.id,
                         id_video=video.id, value=value)
        db.session.add(vote)
    else:
        vote.value = value


def round_is_open(run, testers=None):
    if run.phase != "running" or run.round_started is None:
        return False
    if time.time() >= run.round_started + ROUND_SECONDS:
        return False
    video = _current_video(run)
    if video is None:
        return False
    if testers is None:
        testers = _testers(run)
    voted = {vote.id_tester for vote in _votes_of_video(run, video)}
    return any(tester.id not in voted for tester in testers)


def _sync_last_seq(testers, seq):
    for tester in testers:
        tester.last_seq = seq


def process_events(run, listener):
    """Turn listener events into pairing and votes; returns True on change."""
    testers = _testers(run)
    events = sorted(listener.get("events") or [], key=lambda event: event.get("seq", 0))
    names = {device.get("id"): device.get("name")
             for device in listener.get("devices") or []}
    changed = False

    if run.pairing_seat is not None:
        tester = _tester(run, run.pairing_seat)
        taken = {tester.keyboard_id for tester in testers if tester.keyboard_id}
        newest = max((tester.last_seq or 0) for tester in testers) if testers else 0
        if tester is not None:
            for event in events:
                device_id = event.get("device_id")
                if event.get("seq", 0) <= newest or not device_id or device_id in taken:
                    continue
                tester.keyboard_id = device_id
                tester.keyboard_name = names.get(device_id) or device_id
                tester.last_seq = event["seq"]
                run.pairing_seat = None
                changed = True
                break

    if round_is_open(run, testers):
        video = _current_video(run)
        for tester in testers:
            if not tester.keyboard_id:
                continue
            for event in events:
                if event.get("seq", 0) <= (tester.last_seq or 0):
                    continue
                if event.get("device_id") != tester.keyboard_id:
                    continue
                tester.last_seq = event["seq"]
                value = VOTE_KEYS.get(event.get("key"))
                if value is not None:
                    _store_vote(run, tester, video, value)
                changed = True

    if changed:
        db.session.commit()
    return changed


def generate_order(session):
    """The shared video order; the algorithm is copied from the old test flow."""
    sequences = Sequence.query.filter_by(id_session=session.id).all()
    i = 0
    for sequence in sequences:
        if session.test_method == "dcr":
            sequences[i] = Video.query.filter_by(id_sequence=sequence.id).filter(Video.reference == False).all()
        else:
            sequences[i] = Video.query.filter_by(id_sequence=sequence.id).all()
        i = i + 1

    sequences_order = []

    for i in range(len(sequences)):
        sequences_order = sequences_order + [i + 1] * len(sequences[i])

    if not sequences_order:
        return []

    again = True

    while again:
        random.shuffle(sequences_order)

        for i in range(len(sequences_order) - 2):
            zmena = True
            while zmena:
                zmena = False
                if sequences_order[i] == sequences_order[i + 1]:
                    pom = sequences_order[i + 1]
                    sequences_order[i + 1] = sequences_order[i + 2]
                    sequences_order[i + 2] = pom
                    zmena = True
                else:
                    again = False
                if sequences_order[i] == sequences_order[i + 1] == sequences_order[i + 2]:
                    random.shuffle(sequences_order)
                    again = True
                    break
                if sequences_order[i + 1] == sequences_order[i + 2]:
                    again = True
                    break

    video = [0] * len(sequences)
    for i in range(len(sequences)):
        random.shuffle(sequences[i])

    order = []
    for i in range(len(sequences_order)):
        order.append(sequences[(sequences_order[i] - 1)][video[(sequences_order[i] - 1)]].id)
        video[(sequences_order[i] - 1)] = int(video[(sequences_order[i] - 1)]) + 1
    return order


def _round_paths(session, video):
    """Files mpv plays for one round, or None if any of them is missing."""
    folder_name = session.name.replace(" ", "_")
    folder = "ref_seq" if video.reference else "test_seq"
    current_path = video_path(folder_name, folder, video.name)
    if not os.path.exists(current_path):
        return None
    if session.test_method != "dcr":
        return [current_path]
    reference = Video.query.filter_by(id_sequence=video.id_sequence,
                                      reference=True).first()
    grey = video_path("grey50.mp4")
    if reference is None or not os.path.exists(grey):
        return None
    reference_path = video_path(folder_name, "ref_seq", reference.name)
    if not os.path.exists(reference_path):
        return None
    return [reference_path, grey, current_path]


# ---------- setup ---------------------------------------------------------

@group.route('/<int:id_session>')
@login_required
@role_required(10)
def setup(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = _run_for(session)
    return render_template("group_setup.html", user=current_user, session=session,
                           run=run, max_testers=MAX_TESTERS)


@group.route('/<int:id_session>/tester', methods=['POST'])
@login_required
@role_required(10)
def save_tester(id_session):
    session = _owned_session(id_session)
    if session is None:
        return jsonify({"error": "forbidden"}), 403
    run = _run_for(session)
    data = _payload()
    seat = _parse_int(data.get("seat"))
    if seat is None or not 1 <= seat <= MAX_TESTERS:
        return jsonify({"error": f"seat must be 1..{MAX_TESTERS}"}), 400

    tester = _ensure_tester(run, seat)
    if "name" in data:
        tester.name = _clean_name(data.get("name"))
    if "age" in data:
        tester.age = _parse_int(data.get("age"))
    if "glasses" in data:
        tester.glasses = _parse_bool(data.get("glasses"))
    if "gender" in data:
        gender = (data.get("gender") or "").strip().lower()
        tester.gender = gender[:1] or None
    db.session.commit()
    return jsonify({"ok": True, "seat": seat, "name": tester.name,
                    "age": tester.age, "glasses": tester.glasses})


@group.route('/<int:id_session>/pair', methods=['POST'])
@login_required
@role_required(10)
def pair(id_session):
    session = _owned_session(id_session)
    if session is None:
        return jsonify({"error": "forbidden"}), 403
    run = _run_for(session)
    seat = _parse_int(_payload().get("seat"))
    if seat is None or not 1 <= seat <= MAX_TESTERS:
        return jsonify({"error": f"seat must be 1..{MAX_TESTERS}"}), 400
    _ensure_tester(run, seat)
    # Ignore everything already in the listener buffer: only a key pressed
    # after this request may bind. Same cursor trick as at the start of a round.
    _sync_last_seq(_testers(run), keyboards.state().get("seq", 0))
    run.pairing_seat = seat
    db.session.commit()
    return jsonify({"ok": True, "pairing_seat": seat})


@group.route('/<int:id_session>/add', methods=['POST'])
@login_required
@role_required(10)
def add_tester(id_session):
    session = _owned_session(id_session)
    if session is None:
        return jsonify({"error": "forbidden"}), 403
    run = _run_for(session)
    seats = {tester.seat for tester in _testers(run)}
    if len(seats) >= MAX_TESTERS:
        return jsonify({"error": f"maximum is {MAX_TESTERS} testers"}), 400
    seat = next(number for number in range(1, MAX_TESTERS + 1) if number not in seats)
    _ensure_tester(run, seat)
    return jsonify({"ok": True, "seat": seat})


@group.route('/<int:id_session>/remove', methods=['POST'])
@login_required
@role_required(10)
def remove_tester(id_session):
    """Delete one tester and renumber the rest to 1..N, so the free seats are
    always at the end and a new tester gets the next number."""
    session = _owned_session(id_session)
    if session is None:
        return jsonify({"error": "forbidden"}), 403
    run = _run_for(session)
    if run.phase == "running":
        return jsonify({"error": "testers cannot be removed during a test"}), 409
    seat = _parse_int(_payload().get("seat"))
    tester = _tester(run, seat) if seat is not None else None
    if tester is None:
        return jsonify({"error": "no tester on this seat"}), 404

    GroupVote.query.filter_by(id_tester=tester.id).delete()
    db.session.delete(tester)
    db.session.flush()

    if run.pairing_seat == seat:
        run.pairing_seat = None
    renumbered = {}
    for number, other in enumerate(_testers(run), start=1):
        if other.seat != number:
            renumbered[other.seat] = number
            other.seat = number
    if run.pairing_seat in renumbered:
        run.pairing_seat = renumbered[run.pairing_seat]
    db.session.commit()
    return jsonify({"ok": True, "removed": seat, "renumbered": renumbered,
                    "count": len(_testers(run))})


@group.route('/<int:id_session>/start', methods=['POST'])
@login_required
@role_required(10)
def start(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = _run_for(session)
    testers = _testers(run)
    if not testers:
        flash('Add at least one tester before starting.', category='error')
        return redirect(url_for('group.setup', id_session=session.id))
    missing = [str(tester.seat) for tester in testers if not tester.name]
    if missing:
        flash('Tester ' + ', '.join(missing) + ' has no name.', category='error')
        return redirect(url_for('group.setup', id_session=session.id))
    missing = [str(tester.seat) for tester in testers if tester.age is None]
    if missing:
        flash('Tester ' + ', '.join(missing) + ' has no age.', category='error')
        return redirect(url_for('group.setup', id_session=session.id))

    order = generate_order(session)
    if not order:
        flash('This session has no videos to test.', category='error')
        return redirect(url_for('group.setup', id_session=session.id))
    # Check every file before the run switches to "running"; otherwise a missing
    # video left the run stuck in "running" and testers could not be edited.
    for video_id in order:
        video = Video.query.filter_by(id=video_id).first()
        if video is None or _round_paths(session, video) is None:
            flash('Some videos of this session are missing in the video folder '
                  '(or grey50.mp4 is missing). Copy them there and press Start again.',
                  category='error')
            return redirect(url_for('group.setup', id_session=session.id))

    # a second run must not inherit the votes of the previous one
    GroupVote.query.filter_by(id_group_run=run.id).delete()
    run.order = ", ".join(str(video_id) for video_id in order)
    run.current_id = 0
    run.phase = "running"
    run.round_started = None
    run.pairing_seat = None
    _sync_last_seq(testers, keyboards.state().get("seq", 0))
    db.session.commit()
    return redirect(url_for('group.play', id_session=session.id))


@group.route('/<int:id_session>/training', methods=['POST'])
@login_required
@role_required(10)
def training(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = _run_for(session)
    folder_name = session.name.replace(" ", "_")
    trainings = Training.query.filter_by(id_session=session.id, ref=False).all()
    paths = []

    if session.test_method == "dcr":
        reference = Training.query.filter_by(id_session=session.id, ref=True).first()
        grey = video_path("grey50.mp4")
        if reference is None or not os.path.exists(grey):
            return redirect(url_for('views.problem'))
        reference_path = video_path(folder_name, "training", reference.name)
        if not os.path.exists(reference_path):
            return redirect(url_for('views.problem'))
        for item in trainings:
            current_path = video_path(folder_name, "training", item.name)
            if not os.path.exists(current_path):
                return redirect(url_for('views.problem'))
            paths = paths + [reference_path, grey, current_path]
    else:
        for item in trainings:
            current_path = video_path(folder_name, "training", item.name)
            if not os.path.exists(current_path):
                return redirect(url_for('views.problem'))
            paths.append(current_path)

    if paths:
        play_videos(*paths)
    flash('Training finished', category='success')
    return redirect(url_for('group.setup', id_session=session.id))


@group.route('/<int:id_session>/reset', methods=['POST'])
@login_required
@role_required(10)
def reset(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = GroupRun.query.filter_by(id_session=session.id).first()
    if run is not None:
        db.session.delete(run)
        db.session.commit()
    flash('Group run reset', category='success')
    return redirect(url_for('group.setup', id_session=session.id))


# ---------- state ---------------------------------------------------------

@group.route('/<int:id_session>/state')
@login_required
@role_required(10)
def state(id_session):
    session = _owned_session(id_session)
    if session is None:
        return jsonify({"error": "forbidden"}), 403
    run = _run_for(session)
    listener = keyboards.state()
    process_events(run, listener)

    testers = _testers(run)
    order = _order_ids(run)
    video = _current_video(run) if run.phase == "running" else None
    open_round = round_is_open(run, testers)
    current_votes = {}
    if video is not None:
        current_votes = {vote.id_tester: vote.value
                         for vote in _votes_of_video(run, video)}
    since = request.args.get("since", 0, type=int) or 0

    seconds_left = 0.0
    if run.round_started is not None:
        seconds_left = max(0.0, run.round_started + ROUND_SECONDS - time.time())

    tester_rows = []
    for tester in testers:
        # only this round counts: a tester who missed it shows nothing, not the
        # value from some earlier video
        vote = current_votes.get(tester.id)
        tester_rows.append({
            "id": tester.id,
            "seat": tester.seat,
            "keyboard_id": tester.keyboard_id,
            "keyboard_name": tester.keyboard_name,
            "name": tester.name,
            "age": tester.age,
            "glasses": tester.glasses,
            "gender": tester.gender,
            "vote": vote,
            "last_seq": tester.last_seq,
        })

    method, labels = _scale(session)
    return jsonify({
        "phase": run.phase,
        "listener": listener.get("listener", False),
        "park": {
            "id": video.id if video is not None else None,
            "current": run.current_id + 1 if order else 0,
            "total": len(order),
            "seconds_left": round(seconds_left, 1),
            "round_open": open_round,
        },
        "scale": {"method": method, "labels": labels},
        "testers": tester_rows,
        "events": [event for event in listener.get("events") or []
                   if event.get("seq", 0) > since],
        "pairing_seat": run.pairing_seat,
    })


# ---------- rounds --------------------------------------------------------

@group.route('/<int:id_session>/play')
@login_required
@role_required(10)
def play(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = _run_for(session)
    if run.phase == "finished":
        return redirect(url_for('group.results', id_session=session.id))
    if run.phase != "running":
        return redirect(url_for('group.setup', id_session=session.id))

    video = _current_video(run)
    if video is None:
        return redirect(url_for('group.results', id_session=session.id))

    paths = _round_paths(session, video)
    if paths is None:
        return redirect(url_for('views.problem'))
    play_videos(*paths)

    run.round_started = time.time()
    _sync_last_seq(_testers(run), keyboards.state().get("seq", 0))
    db.session.commit()

    return render_template("group_vote.html", user=current_user, session=session,
                           run=run, total=len(_order_ids(run)),
                           current=run.current_id + 1)


@group.route('/<int:id_session>/vote', methods=['POST'])
@login_required
@role_required(10)
def vote(id_session):
    session = _owned_session(id_session)
    if session is None:
        return jsonify({"error": "forbidden"}), 403
    run = _run_for(session)
    data = _payload()
    seat = _parse_int(data.get("seat"))
    value = _parse_int(data.get("value"))
    if seat is None or value not in (1, 2, 3, 4, 5):
        return jsonify({"error": "seat and value 1..5 are required"}), 400
    tester = _tester(run, seat)
    video = _current_video(run)
    if tester is None or video is None or not round_is_open(run):
        return jsonify({"error": "round is not open"}), 409
    _store_vote(run, tester, video, value)
    db.session.commit()
    return jsonify({"ok": True, "seat": seat, "value": value})


@group.route('/<int:id_session>/next', methods=['POST'])
@login_required
@role_required(10)
def next_video(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = _run_for(session)
    if run.phase != "running":
        return redirect(url_for('group.results', id_session=session.id))

    run.current_id = run.current_id + 1
    run.round_started = None
    if run.current_id >= len(_order_ids(run)):
        run.phase = "finished"
        db.session.commit()
        return redirect(url_for('group.results', id_session=session.id))
    db.session.commit()
    return redirect(url_for('group.play', id_session=session.id))


# ---------- results and CSV ----------------------------------------------

@group.route('/<int:id_session>/results')
@login_required
@role_required(10)
def results(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = GroupRun.query.filter_by(id_session=session.id).first()
    if run is None:
        return redirect(url_for('group.setup', id_session=session.id))

    testers = _testers(run)
    rows = []
    for video_id in _order_ids(run):
        video = Video.query.filter_by(id=video_id).first()
        if video is None:
            continue
        votes = {vote.id_tester: vote.value for vote in _votes_of_video(run, video)}
        rows.append({"video": video.name,
                     "votes": [votes.get(tester.id) for tester in testers]})

    return render_template("group_results.html", user=current_user, session=session,
                           run=run, testers=testers, rows=rows)


@group.route('/<int:id_session>/export')
@login_required
@role_required(10)
def export(id_session):
    session = _owned_session(id_session)
    if session is None:
        return redirect(url_for('views.forbidden'))
    run = GroupRun.query.filter_by(id_session=session.id).first()
    if run is None:
        return redirect(url_for('group.setup', id_session=session.id))

    testers = _testers(run)
    videos = []
    for sequence in Sequence.query.filter_by(id_session=session.id).all():
        query = Video.query.filter_by(id_sequence=sequence.id)
        if session.test_method == "dcr":
            query = query.filter_by(reference=False)
        videos.extend(query.all())
    votes = {(vote.id_tester, vote.id_video): vote.value
             for vote in GroupVote.query.filter_by(id_group_run=run.id).all()}
    _, labels = _scale(session)
    table = export_files.build_table(session, testers, videos, votes, labels)

    folder_path = os.path.join(os.getcwd(), "csv")
    os.makedirs(folder_path, exist_ok=True)
    session_name = session.name.replace(" ", "_")
    csv_file_path = os.path.join(folder_path, session_name + ".csv")
    xlsx_file_path = os.path.join(folder_path, session_name + ".xlsx")

    try:
        export_files.write_csv(table, csv_file_path)
    except PermissionError:
        flash(f'Cannot write {session_name}.csv — close it in Excel and export again.',
              category='error')
        return redirect(url_for('group.results', id_session=session.id))

    try:
        export_files.write_xlsx(table, xlsx_file_path)
    except ImportError:
        flash('CSV exported. For the Excel file run: pip install -r requirements.txt',
              category='error')
        open_folder("csv")
        return redirect(url_for('group.results', id_session=session.id))
    except PermissionError:
        flash(f'CSV exported, but {session_name}.xlsx is open in Excel — close it '
              'and export again.', category='error')
        open_folder("csv")
        return redirect(url_for('group.results', id_session=session.id))

    open_folder("csv")
    flash('CSV and Excel exported into csv folder', category='success')
    return redirect(url_for('group.results', id_session=session.id))
