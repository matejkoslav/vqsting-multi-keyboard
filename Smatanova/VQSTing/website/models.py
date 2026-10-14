from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Integer)
    details = db.relationship('Detail', backref='user', lazy=True)
    sessions = db.relationship('Session', backref='user', lazy=True)
    valuations = db.relationship('Valuation', backref='user', lazy=True)
    completeds = db.relationship('Completed', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Detail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gender = db.Column(db.String(1))
    age = db.Column(db.Integer)
    glasses = db.Column(db.Boolean)
    
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
    completeds = db.relationship('Completed', backref='session', lazy=True)
    trainings = db.relationship('Training', backref='session', lazy=True)
    orders = db.relationship('Order', backref='session', lazy=True)

class Sequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    videos = db.relationship('Video', backref='sequence', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_sequence = db.Column(db.Integer, db.ForeignKey('sequence.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    reference = db.Column(db.Boolean)
    valuations = db.relationship('Valuation', backref='video', lazy=True)

class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    max = db.Column(db.Integer)
    min = db.Column(db.Integer)
    ref = db.Column(db.Boolean)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_id = db.Column(db.Integer, nullable=False)
    order = db.Column(db.String)

class Valuation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id_video = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    value = db.Column(db.Integer)

class Completed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id_session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())



