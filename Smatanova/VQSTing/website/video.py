from flask import Blueprint, render_template, request, redirect, url_for, make_response, flash
from flask_login import login_required, current_user
from . import db, role_required
from .models import User, Detail, Session, Sequence, Video, Valuation, Completed, Training, Order
import os
import csv
from io import StringIO
import subprocess
from random import randint
from sqlalchemy import and_
import random


video = Blueprint('video', __name__)

@video.route('training/<int:id_session>')
@login_required
@role_required(1)
def training(id_session):
    this_session=Session.query.filter_by(id=id_session).first()
    if this_session.ok == False:
        return redirect(url_for('views.problem'))
    global training_video_id
    training_video_id = 0
    return render_template("training.html",user=current_user,id_session=id_session)

@video.route('/training_start/<int:id_session>')
@login_required
@role_required(1)
def training_play(id_session):
    global training_videos
    global training_video_id
    global scale

    session = Session.query.filter_by(id=id_session).first()
    if session.ok == False:
        return redirect(url_for('views.problem'))
    training_videos = Training.query.filter_by(id_session=id_session).filter_by(ref=False).all()   

    folder_name = session.name.replace(" ","_")
    def_path = "video\\" + folder_name + "\\training"

    print(def_path)

    if not os.path.exists(def_path):
        return redirect(url_for('views.problem'))

    grey = "video\\grey50.mp4"
    if not os.path.exists(grey):
        return redirect(url_for('views.problem'))

    if session.test_method == "dcr":
        ref_video = Training.query.filter_by(id_session=id_session, ref=True).first()
        folder_name = session.name.replace(" ","_")
        ref_video_path = "video\\" + folder_name + "\\training\\" + ref_video.name
        if not os.path.exists(ref_video_path):
            return redirect(url_for('views.problem'))
        
        video_path =ref_video_path + " " + grey + " " + def_path + "\\" + training_videos[training_video_id].name
        if not os.path.exists(def_path + "\\" + training_videos[training_video_id].name):
            return redirect(url_for('views.problem'))
        
        scale = ["32rem", "IMPERCEPTIBLE", "PERCEPTIBLE BUT NOT ANNOYING", "SLIGHTLY ANNOYING", "ANNOYING", "VERY ANNOYING"]
    else:
        video_path = def_path + "\\" + training_videos[training_video_id].name
        if not os.path.exists(video_path):
            return redirect(url_for('views.problem'))
        scale = ["15rem", "EXCELLENT", "GOOD", "FAIR", "POOR", "BAD"]

    subprocess.call(("mpv.exe  --cursor-autohide=0 --osc=no --no-input-default-bindings --ontop --fs {filename}")
                    .format(filename=video_path))
    
    return redirect(url_for('video.valuation_training',id_session=id_session, min=training_videos[training_video_id].min, max=training_videos[training_video_id].max))
 
@video.route("/valuation-training/<int:id_session>/<int:min>/<int:max>", methods=['GET','POST'])
@login_required
@role_required(1)
def valuation_training(id_session,min,max):
    global training_videos
    global training_video_id
    global scale
    session = Session.query.filter_by(id=id_session).first()
    if session.ok == False:
        return redirect(url_for('views.problem'))

    if request.method == "POST":
        rating = request.form.get("value")
        if rating is None:
            rating=0
        if int(rating)>max or int(rating)<min:
            return render_template("repeat-test.html", user=current_user, id_session=id_session)
        training_video_id += 1
        if training_video_id >= len(training_videos):
            return render_template("start.html", user=current_user, id_session=id_session)
        return redirect(url_for('video.training_play', id_session=id_session))

    return render_template("test.html", user=current_user, scale=scale, current=training_video_id+1)

def array_to_string(array):
    return ', '.join(map(str, array))
    
def string_to_array(string):
    split_string = string.split(',')
    return [int(item.strip()) for item in split_string]

@video.route('/test/<int:id>')
@login_required
@role_required(1)
def start(id):    
    session = Session.query.filter_by(id=id).first()
    if session.ok == False:
        return redirect(url_for('views.problem'))
    
    order_obj = Order.query.filter_by(id_session=id).filter_by(id_user=current_user.id).first()

    if order_obj is None:        
        sequences = Sequence.query.filter_by(id_session=id).all()
        i=0
        for sequence in sequences:
            if session.test_method == "dcr":
                sequences[i] = Video.query.filter_by(id_sequence=sequence.id).filter(Video.reference==False).all()
            else:
                sequences[i]=Video.query.filter_by(id_sequence=sequence.id).all()
            i=i+1

        print(sequences)
        sequences_order = []

        for i in range(len(sequences)):
            sequences_order = sequences_order + [i+1]*len(sequences[i])

        again = True

        while again:
            random.shuffle(sequences_order)
            print(sequences_order)

            for i in range(len(sequences_order)-2):
                zmena=True
                while zmena:
                    zmena=False
                    if sequences_order[i]==sequences_order[i+1]:
                        pom = sequences_order[i+1]
                        sequences_order[i+1]=sequences_order[i+2]
                        sequences_order[i+2]=pom
                        zmena=True
                    else:                
                        again=False
                    if sequences_order[i]==sequences_order[i+1]==sequences_order[i+2]:
                        random.shuffle(sequences_order)
                        again=True
                        break
                    if sequences_order[i+1]==sequences_order[i+2]:
                        again=True
                        break

        print(sequences_order)

        video = [0]*len(sequences)
        for i in range(len(sequences)):
            random.shuffle(sequences[i])
            print(sequences[i])

        order = []
        for i in range(len(sequences_order)):
            order.append(sequences[(sequences_order[i]-1)][video[(sequences_order[i]-1)]].id)
            video[(sequences_order[i]-1)]=int(video[(sequences_order[i]-1)])+1
        print(order)

        order_obj = Order(id_session=id, id_user=current_user.id,current_id=0,order=array_to_string(order))
        db.session.add(order_obj)
        db.session.commit()

    return redirect(url_for('video.video_play', id_session=id))

@video.route("/video_play/<int:id_session>")
@login_required
@role_required(1) 
def video_play(id_session):
    global scale

    session = Session.query.filter_by(id=id_session).first()
    if session.ok == False:
        return redirect(url_for('views.problem'))
    
    order_obj = Order.query.filter_by(id_session=id_session).filter_by(id_user=current_user.id).first()
    order = string_to_array(order_obj.order)
    video = Video.query.filter_by(id=order[order_obj.current_id]).first()

    folder_name = session.name.replace(" ","_")

    if video.reference:
        def_path = "video\\" + folder_name + "\\ref_seq"
    else:
        def_path = "video\\" + folder_name + "\\test_seq"
    if not os.path.exists(def_path):
        return redirect(url_for('views.problem'))
    grey = "video\\grey50.mp4"
    if not os.path.exists(grey):
        return redirect(url_for('views.problem'))

    if session.test_method == "dcr":
        sequence_id = video.id_sequence
        ref_video = db.session.query(Video.name).filter(and_(Video.id_sequence == sequence_id, Video.reference == True)).first()
        ref_video_path = "video\\" + folder_name + "\\ref_seq\\" + ref_video[0]
        if not os.path.exists(ref_video_path):
            return redirect(url_for('views.problem'))
        video_path =ref_video_path + " " + grey + " " + def_path + "\\" + video.name  
        if not os.path.exists(def_path + "\\" + video.name):
            return redirect(url_for('views.problem'))     
        scale = ["32rem", "IMPERCEPTIBLE", "PERCEPTIBLE BUT NOT ANNOYING", "SLIGHTLY ANNOYING", "ANNOYING", "VERY ANNOYING"]
    else:
        video_path = def_path + "\\" + video.name
        if not os.path.exists(video_path):
            return redirect(url_for('views.problem'))
        scale = ["15rem", "EXCELLENT", "GOOD", "FAIR", "POOR", "BAD"]

    print(video_path)

    subprocess.call(("mpv.exe  --cursor-autohide=0 --osc=no --no-input-default-bindings --ontop --fs {filename}")
                    .format(filename=video_path))
    
    return redirect(url_for('video.valuation',id_session=id_session,id_video=video.id))
    

@video.route("/valuation_test/<int:id_session>/<int:id_video>", methods=['GET','POST'])
@login_required
@role_required(1) 
def valuation(id_session,id_video):
    global scale

    order_obj = Order.query.filter_by(id_session=id_session).filter_by(id_user=current_user.id).first()
    order = string_to_array(order_obj.order)

    session = Session.query.filter_by(id=id_session).first()
    if session.ok == False:
        return redirect(url_for('views.problem'))

    if request.method == "POST":
        rating = request.form.get("value")
        if rating is None:
            rating=0
        valuation = Valuation(id_user=current_user.id, id_video=id_video, value=rating)
        db.session.add(valuation)
        db.session.commit()
        order_obj.current_id += 1
        db.session.commit()
        if order_obj.current_id >= len(order):
            completed = Completed(id_user=current_user.id,id_session=id_session)
            db.session.add(completed)
            db.session.commit()
            return render_template("finished.html", user=current_user)
        return redirect(url_for('video.video_play', id_session=id_session))

    return render_template("test.html", user=current_user, scale=scale, current=int(order_obj.current_id)+1)

@video.route("/export/<int:id>")
@login_required
@role_required(10) 
def export(id):

    session = Session.query.filter_by(id=id).first()
    sequences = Sequence.query.filter_by(id_session=id).all()
    folder_path = os.path.join("csv")
    os.makedirs(folder_path, exist_ok=True)
    subprocess.call(["start", folder_path], shell=True)
    session_name = session.name.replace(" ","_")
    csv_file_path = os.path.join(os.getcwd(), "csv", session_name + ".csv")
    
    with open(csv_file_path, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([session.name])
        csv_writer.writerow([session.test_method, session.display])
        csv_writer.writerow([])

        for sequence in sequences:
            if session.test_method=="dcr":
                all_videos = Video.query.filter_by(id_sequence = sequence.id).filter_by(reference = False).all()
            else:
                all_videos = Video.query.filter_by(id_sequence = sequence.id).all()
            for video in all_videos:
                all_data = Valuation.query.filter_by(id_video=video.id).all()
                csv_row = [video.name]
                for data in all_data:
                    if data.value == 0:
                        csv_row.append("n/a")
                    else:
                        csv_row.append(data.value)
                csv_writer.writerow(csv_row)
    flash('CSV exported into csv folder', 'success')
    return redirect(url_for('views.my_table_sessions'))
