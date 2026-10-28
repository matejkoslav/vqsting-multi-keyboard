from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Integer)
    sessions = db.relationship('Session', backref='user', lazy=True)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    test_method = db.Column(db.String(3))
    display = db.Column(db.String(200))
    surrounding = db.Column(db.String(10))
    password = db.Column(db.String(200), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ok = db.Column(db.Boolean)
    sequences = db.relationship('Sequence', backref='session', lazy=True)
    trainings = db.relationship('Training', backref='session', lazy=True)


class Sequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    videos = db.relationship('Video', backref='sequence', lazy=True)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_sequence = db.Column(db.Integer, db.ForeignKey('sequence.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    reference = db.Column(db.Boolean)


class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    max = db.Column(db.Integer)
    min = db.Column(db.Integer)
    ref = db.Column(db.Boolean)


class GroupRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False, unique=True)
    order = db.Column(db.String, default="")
    current_id = db.Column(db.Integer, nullable=False, default=0)
    phase = db.Column(db.String(10), nullable=False, default="setup")
    round_started = db.Column(db.Float)
    pairing_seat = db.Column(db.Integer)
    created = db.Column(db.DateTime(timezone=True), default=func.now())
    testers = db.relationship('Tester', backref='group_run', lazy=True,
                              cascade='all, delete-orphan')
    votes = db.relationship('GroupVote', backref='group_run', lazy=True,
                            cascade='all, delete-orphan')


class Tester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_group_run = db.Column(db.Integer, db.ForeignKey('group_run.id'), nullable=False)
    seat = db.Column(db.Integer, nullable=False)
    keyboard_id = db.Column(db.String(200))
    keyboard_name = db.Column(db.String(200))
    age = db.Column(db.Integer)
    glasses = db.Column(db.Boolean)
    gender = db.Column(db.String(1))
    last_seq = db.Column(db.Integer, nullable=False, default=0)


class GroupVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_group_run = db.Column(db.Integer, db.ForeignKey('group_run.id'), nullable=False)
    id_tester = db.Column(db.Integer, db.ForeignKey('tester.id'), nullable=False)
    id_video = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)
