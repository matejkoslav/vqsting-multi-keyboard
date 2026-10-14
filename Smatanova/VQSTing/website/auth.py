from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Detail
from . import db, role_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('User doesn\'t exist', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/register', methods=['GET', 'POST'])
def register():

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
            return redirect(url_for('auth.profile'))
        
        
    return render_template("register.html", user='false', role=1)



@auth.route('/profile', methods=['GET','POST'])
@login_required
@role_required(1) 
def profile():

    if request.method=='POST':
        
        gender = request.form.get('gender')
        age = request.form.get('age')
        glasses = request.form.get('glasses')
    
        if gender is None:
            flash('Please select gender!', category='error')
        elif age is None:
            flash('Please enter your age!', category='error')
        elif int(age) < 15 :
            flash('You have to be at least 15 years old!', category='error')
        elif glasses is None:
            flash('Please check whether you wear glasses or lens', category='error')
        else:
            profile = Detail(id_user=current_user.id,gender=gender,age=int(age), glasses=eval(glasses))
            db.session.add(profile)
            db.session.commit()

            flash('Profile updated!', category='success')
            return redirect(url_for('views.profile_info'))        

    return render_template("profile.html", user=current_user)


@auth.route('/profile-update', methods=['GET', 'POST'])
@login_required
@role_required(1) 
def update():
    detail=Detail.query.filter_by(id_user=current_user.id).first()

    if request.method=='POST':
        gender = request.form.get('gender')
        age = request.form.get('age')
        glasses = request.form.get('glasses')

        if gender is None:
            flash('Please choose gender!', category='error')
        elif age is "":
            flash('Please enter your age!', category='error')
        elif int(age) < 15:
            flash('You have to be at least 15 years old!', category='error')
        elif glasses is None:
            flash('Please check whether you wear glasses or lens', category='error')
        else:
            if detail:    
                detail.gender = gender
                detail.age = int(age)
                detail.glasses = eval(glasses)
            else:
                profile = Detail(id_user=current_user.id,gender=gender,age=int(age), glasses=eval(glasses))
                db.session.add(profile)        
            db.session.commit()

            flash('Profile updated!', category='success')
            return redirect(url_for('views.profile_info'))        

    return render_template("profile-edit.html", user=current_user, detail=detail)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))