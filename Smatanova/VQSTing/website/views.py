from flask import Blueprint, render_template, request, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from . import db, role_required
from .models import User, Detail, Session, Sequence, Video, Valuation, Completed, Training
import os
import subprocess
import random
import time
from sqlalchemy import func

import plotly.graph_objs as go

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html", user=current_user)

@views.route('/forbidden')
def forbidden():
    return render_template("errors/forbidden.html", user=current_user)

@views.route('/problem')
def problem():
    return render_template("errors/session-problem.html", user=current_user)

@views.route('/profile-info')
@login_required
@role_required(1) 
def profile_info():
    return render_template("profile-info.html", user=current_user)

@views.route('/create-test', methods=['GET','POST'])
@login_required
@role_required(10) 
def create_test():
    if request.method=='POST':
        
        name = request.form.get('name')
        test_method = request.form.get('test_method')
        display = request.form.get('display')
        surrounding = request.form.get('surroundings')
        password = request.form.get('password')

        session = Session.query.filter_by(name=name).first()
        if session:
            flash('Session with this name already exists', category='error')        
        elif len(name) < 4:
            flash('Name must be greater than 3 characters.', category='error')
        elif len(password) < 5:
            flash('Password must be at least 5 characters.', category='error')
        else:
            new_session = Session(name=name,test_method=test_method,display=display,surrounding=surrounding,password=password,id_user=current_user.id, ok=False)
            db.session.add(new_session)
            db.session.commit()

            folder_name = name.replace(" ","_")

            folder_path = os.path.join("video", folder_name, "test_seq")
            os.makedirs(folder_path, exist_ok=True)

            folder_path = os.path.join("video", folder_name, "training")
            os.makedirs(folder_path, exist_ok=True)

            if test_method != "acr":
                folder_path = os.path.join("video", folder_name, "ref_seq")
                os.makedirs(folder_path, exist_ok=True)

            flash('Session created!', category='success')  

            created_session = Session.query.filter_by(name=name).first()

            return redirect(url_for('views.add_videos', session = created_session.id))
        
    return render_template("create-test.html", user=current_user)

@views.route('/add-videos/<session>', methods=['GET', 'POST'])
@login_required
@role_required(10) 
def add_videos(session):
    try:
        this_session = Session.query.filter_by(id=session).first()
        folder_path = os.path.join("video", this_session.name)
        subprocess.call(["start", folder_path], shell=True)

        if request.method=='POST':
            letters = request.form.get('letters')
            return redirect(url_for('views.insert_sequences', id = session, letters=letters))
    except:
        return render_template("/errors/error.html", user=current_user)

    return render_template("add-videos.html", user=current_user)

@views.route('/insert-sequences/<int:id>/<int:letters>', methods=['GET', 'POST'])
@login_required
@role_required(10) 
def insert_sequences(id, letters):
    try:
        this_session = Session.query.filter_by(id=id).first()
        folder_name = this_session.name.replace(" ","_")

        path = os.path.join("video", folder_name)

        for r, d, f in os.walk(path):   
            try:
                for folder in d:
                    folder_path = os.path.join(r, folder)
                    files_in_folder = os.listdir(folder_path)

                    if not files_in_folder:
                        this_session.ok = False
                        db.session.commit()
                        flash('Please insert videos into all folders in created directory')
                        return redirect(url_for('views.add_videos', session=this_session))

                for file in f:

                    folder = r.split("\\")

                    if  folder[2]=="training":
                        training = Training(id_session=this_session.id, name=str(file), max=5, min=1, ref=False)
                        db.session.add(training)
                        db.session.commit()
                    else:

                        pattern = file[0:letters]
                        print(pattern)
                        sequence = None

                        all_sequences = db.session.query(Sequence.id).filter(Sequence.id_session==id).all()
                        videos_in_sequence = db.session.query(Video.id_sequence).filter(Video.name.like(pattern + "%")).all()
                        #videos_in_sequence = db.session.query(Video.id_sequence).filter(Video.name.startswith(pattern)).all()       

                        if videos_in_sequence != []:
                            for video in videos_in_sequence:
                                if video in all_sequences:
                                    sequence = Sequence.query.filter_by(id=video[0]).first()
                                    break
                        if sequence is None:    
                            sequence = Sequence(id_session=this_session.id)
                            db.session.add(sequence)
                            db.session.commit()
                            sequence = Sequence.query.filter_by(id_session=this_session.id).order_by(Sequence.id.desc()).first()
                        if (folder[2]=="ref_seq"):
                            reference=True
                        else:
                            reference=False

                        new_video = Video(id_sequence=sequence.id, name=str(file), reference=reference)
                        db.session.add(new_video)
                        db.session.commit()
                this_session.ok=True
                db.session.commit()                
            except:
                flash('Error',category="error")            
        flash('Session completed', category="success")
    except:
        return render_template("/errors/error.html", user=current_user)
    return redirect(url_for('views.set_training', id=id))

@views.route('/set-training/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(10) 
def set_training(id):
    session = Session.query.filter_by(id=id).first()

    if session.id_user!=current_user.id:
        return redirect(url_for('views.forbidden'))

    if request.method=='POST':
        ok = True
        if session.test_method == "dcr":
            ok = False
            reference = request.form.get("reference")
            if reference is None:
                flash('Please select reference!', category='error')
            else:
                ok = True
        if ok:
            for training in session.trainings:
                min_value = request.form.get(f"min_{training.id}")
                max_value = request.form.get(f"max_{training.id}")
                reference = False
                if request.form.get(f"reference"):
                    reference_id = request.form.get(f"reference")
                    if reference_id == f"reference_{training.id}":
                        reference = True
                training.min = min_value
                training.max = max_value
                training.ref = reference
                db.session.add(training)
            db.session.commit()
            return redirect(url_for('views.details', id=id))
    
    return render_template('set-training.html', user=current_user, session=session)               

@views.route('/my-table-sessions')
@login_required
@role_required(10)
def my_table_sessions():
    return render_template("my-sessions-table.html", user=current_user)

@views.route('/details/<int:id>')
@login_required
@role_required(10) 
def details(id):
    session = Session.query.filter_by(id=id).first() 
    if session.id_user!=current_user.id:
        return redirect(url_for('views.forbidden'))
    return render_template("session-details.html", user=current_user, session=session)

@views.route('/sessions-list', methods=['GET', 'POST'])
@login_required
@role_required(1) 
def sessions_list():
    if request.method=='POST':
        password = request.form.get('password')
        session_id= request.form.get('session_id')
        session = Session.query.filter_by(id=session_id).first()
        session_password = session.password
        
        if password==session_password:
            return redirect(url_for('video.training', id_session=session_id))
        else:
            flash('Incorrect password', category='error')
            
    all_sessions=Session.query.filter_by(ok=True).all()
    return render_template("sessions-list.html", user=current_user, all_sessions=all_sessions)
    
@views.route('statistics/<int:id>')
@login_required
@role_required(10) 
def statistics(id):
    session = Session.query.filter_by(id=id).first()
    if session.id_user!=current_user.id:
        return redirect(url_for('views.forbidden'))

    colors = ['#4183D7', '#CF000F']

    male = db.session.query(
            func.count(Detail.id)
        ).filter(
            Completed.id_session==id,
        ).filter(
            User.id == Completed.id_user,
        ).filter(
            Detail.id_user==User.id
        ).filter(
            Detail.gender == 'm'
        ).scalar()
    female = db.session.query(
            func.count(Detail.id)
        ).filter(
            Completed.id_session==id,
        ).filter(
            User.id == Completed.id_user,
        ).filter(
            Detail.id_user==User.id
        ).filter(
            Detail.gender == 'f'
        ).scalar()

    values = [male, female]
    labels = ["Man", "Woman"]

    trace = go.Pie(labels=labels, values=values, showlegend=True, textinfo='value', textposition='inside', marker=dict(colors=colors))
    layout = go.Layout(legend=dict(orientation='h', x=0, y=0.1), title=dict(text='Gender', x=0.5, y=0.78),)
    gender_fig = go.Figure(data=[trace], layout=layout)
    gender_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )


    ages = db.session.query(
            Detail.age, func.count(Detail.id)
        ).filter(
            Completed.id_session==id,
        ).filter(
            User.id == Completed.id_user,
        ).filter(
            Detail.id_user==User.id
        ).group_by(
            Detail.age
        ).all()

    age = [row[0] for row in ages]
    count = [row[1] for row in ages]

    trace = go.Bar(x=age, y=count, width=0.5, showlegend=False, text=count, textposition='inside', insidetextanchor='start', marker=dict(color='#4183D7'))
    layout = go.Layout(title=dict(text='Age', x=0.5, y=0.8),  xaxis=dict(tickmode='linear', dtick=2, tickangle=0), yaxis=dict(tickmode='linear', dtick=1))
    age_fig = go.Figure(data=[trace], layout=layout)
    age_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )


    normal = db.session.query(
            func.count(Detail.id)
        ).filter(
            Completed.id_session==id,
        ).filter(
            User.id == Completed.id_user,
        ).filter(
            Detail.id_user==User.id
        ).filter(
            Detail.glasses == False
        ).scalar()
    corrected = db.session.query(
            func.count(Detail.id)
        ).filter(
            Completed.id_session==id,
        ).filter(
            User.id == Completed.id_user,
        ).filter(
            Detail.id_user==User.id
        ).filter(
            Detail.glasses == True
        ).scalar()

    values = [normal, corrected]
    labels = ["Normal", "Corrected"]

    trace = go.Pie(labels=labels, values=values, showlegend=True, textinfo='value', textposition='inside', marker=dict(colors=colors))
    layout = go.Layout(legend=dict(orientation='h', x=0, y=0.1), title=dict(text='Visual acuity', x=0.5, y=0.78),)
    sight_fig = go.Figure(data=[trace], layout=layout)
    sight_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return render_template(
        "statistics.html", user=current_user, session=session, 
        gender=gender_fig.to_html(full_html=False, config={'displayModeBar': False, 'displaylogo': False}),
        sight=sight_fig.to_html(full_html=False, config={'displayModeBar': False, 'displaylogo': False}),
        ages=age_fig.to_html(full_html=False, config={'displayModeBar': False, 'displaylogo': False})
        )
