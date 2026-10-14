from flask import Blueprint, render_template, flash, redirect, url_for, request
from .models import User, Detail, Session, Sequence, Video, Completed, Valuation, Training, Order
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

admin = Blueprint('admin', __name__)

@admin.route('/', methods=['GET', 'POST'])
def register_admin():

    if request.method=='POST':
        
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('confirm_password')
        role = int(request.form.get('role'))

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', category='error')
        elif len(username) < 4:
            flash('Username must be greater than 3 characters.', category='error')
        elif len(password) < 5:
            flash('Password must be at least 5 characters.', category='error')
        elif password != password_confirm:
            flash('Passwords don\'t match.', category='error')
        else:
            new_user = User(username=username,password=generate_password_hash(password, method='pbkdf2'),role=role)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')

            return redirect(url_for('views.home'))
        
    return render_template("register.html", user='false', role=10)


@admin.route('/table-users')
def show_table_users():
    our_users = User.query.all()        
    return render_template("/managing/user-table.html",our_users=our_users, user='false')

def delete_whole_session(id_session):
    sequences_to_delete = Sequence.query.filter_by(id_session=id_session).all()
    trainings_to_delete = Training.query.filter_by(id_session=id_session).all()
    if sequences_to_delete != []:
        for sequence in sequences_to_delete:
            videos_to_delete = Video.query.filter_by(id_sequence=sequence.id).all()
            if videos_to_delete != []:
                for video in videos_to_delete:
                    valuations_to_delete= Valuation.query.filter_by(id_video=video.id).all()
                    if valuations_to_delete != []:
                        for valuation in valuations_to_delete:
                            db.session.delete(valuation)
                            db.session.commit()                     
                    db.session.delete(video)
                    db.session.commit()
            db.session.delete(sequence)
            db.session.commit()
    if trainings_to_delete != []:
        for training in trainings_to_delete:
            db.session.delete(training)
            db.session.commit()

    orders_to_delete=Order.query.filter_by(id_session=id_session).all()
    if orders_to_delete != []:
        for order in orders_to_delete:
            db.session.delete(order)
            db.session.commit()
    completeds_to_delete = Completed.query.filter_by(id_session=id_session).all()
    if completeds_to_delete != []:
        for completed in completeds_to_delete:
            db.session.delete(completed)
            db.session.commit() 


@admin.route('/delete-user/<int:id>')
def delete_user(id):
    user_to_delete = User.query.filter_by(id).first()
    details_to_delete = Detail.query.filter_by(id_user=user_to_delete.id).all()
    sessions_to_delete = Session.query.filter_by(id_user=user_to_delete.id).all()

    try:
        for detail in details_to_delete:
            db.session.delete(detail)
            db.session.commit()

        for session in sessions_to_delete:
            delete_whole_session(session.id)             
            db.session.delete(session)
            db.session.commit()
        
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User deleted successfully", category='success')
        our_users = User.query.all() 
        return redirect(url_for('admin.show_table_users'))       
    except:
        flash("Can not delete user", category='error')
        our_users = User.query.all()  
        return render_template("/managing/user-table.html",our_users=our_users, user='false')
    
@admin.route('/delete-session/<int:id>')
def delete_session(id):
    session_to_delete = Session.query.filter_by(id=id).first()
    

    try:
        delete_whole_session(session_to_delete.id)
        db.session.delete(session_to_delete)
        db.session.commit()
        flash("Session deleted successfully", category='success')      
        return redirect(url_for('views.my_table_sessions'))
    except:
        flash("Can not delete session", category='error')
        return redirect(url_for('views.my_table_sessions'))
    

@admin.route('/delete-valuation/<int:id>/<int:user_id>')
def delete_valuation(id,user_id):

    values_to_delete = Valuation.query.filter(
        Sequence.id_session==id
    ).filter(
        Video.id_sequence==Sequence.id
    ).filter(
        Valuation.id_video==Video.id
    ).filter(
        Valuation.id_user==user_id
    ).all()

    completed = Completed.query.filter(Completed.id_user==user_id).filter(Completed.id_session==id).first()

    print(values_to_delete)
    print(completed)

    try:
        for value in values_to_delete:
            db.session.delete(value)
            db.session.commit()    
        db.session.delete(completed)
        db.session.commit()
        flash("Participant ratings deleted successfully", category='success')      
        return redirect(url_for('views.statistics',id=id))
    except:
        flash("Can not delete participants ratings", category='error')
        return redirect(url_for('views.statistics',id=id))