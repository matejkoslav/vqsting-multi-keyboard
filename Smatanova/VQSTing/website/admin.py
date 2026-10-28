from flask import Blueprint, render_template, flash, redirect, url_for
from .models import User, Session, Sequence, Video, Training, GroupRun
from . import db, role_required
from flask_login import login_required

admin = Blueprint('admin', __name__)


@admin.route('/')
@login_required
@role_required(10)
def admin_home():
    return redirect(url_for('admin.show_table_users'))


@admin.route('/table-users')
def show_table_users():
    our_users = User.query.all()
    return render_template("/managing/user-table.html", our_users=our_users, user='false')


def delete_whole_session(id_session):
    run = GroupRun.query.filter_by(id_session=id_session).first()
    if run is not None:
        db.session.delete(run)
        db.session.commit()

    sequences_to_delete = Sequence.query.filter_by(id_session=id_session).all()
    trainings_to_delete = Training.query.filter_by(id_session=id_session).all()
    if sequences_to_delete != []:
        for sequence in sequences_to_delete:
            videos_to_delete = Video.query.filter_by(id_sequence=sequence.id).all()
            if videos_to_delete != []:
                for video in videos_to_delete:
                    db.session.delete(video)
                    db.session.commit()
            db.session.delete(sequence)
            db.session.commit()
    if trainings_to_delete != []:
        for training in trainings_to_delete:
            db.session.delete(training)
            db.session.commit()


@admin.route('/delete-session/<int:id>')
def delete_session(id):
    session_to_delete = Session.query.filter_by(id=id).first()

    try:
        delete_whole_session(session_to_delete.id)
        db.session.delete(session_to_delete)
        db.session.commit()
        flash("Session deleted successfully", category='success')
        return redirect(url_for('views.my_table_sessions'))
    except Exception:
        flash("Can not delete session", category='error')
        return redirect(url_for('views.my_table_sessions'))
