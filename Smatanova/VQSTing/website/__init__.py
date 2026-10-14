from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, current_user
from datetime import datetime
import math
from functools import wraps

db = SQLAlchemy()
DB_NAME = "database.db"

def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role != role:
                return redirect(url_for('views.forbidden'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def create_app():
    app = Flask(__name__)  #inicialize Flask
    app.config['SECRET_KEY'] = 'fsYdgSF*GG5fd'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.config['REMEMBER_COOKIE_DURATION'] = 3600

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .admin import admin
    from .video import video
    from .models import User, Detail, Session, Sequence, Video, Valuation, Completed, Training, Order

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(video, url_prefix='/')
    

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) #pre primary key
    
    def get_user_name(user_id):
        user = User.query.filter_by(id=user_id).first()
        return user.username if user else 'Unknown User'

    app.jinja_env.globals.update(get_user_name=get_user_name)   

    def get_user_completed(user_id):
        completeds = db.session.query(Completed.id_session).filter_by(id_user=user_id).all()
        return [completed.id_session for completed in completeds]

    app.jinja_env.globals.update(get_user_completed=get_user_completed)  

    def get_completed_date(session_id, user_id):
        date = db.session.query(Completed.date).filter_by(id_session=session_id, id_user=user_id).first()
        date_str = datetime.strftime(date[0], "%d/%m/%Y")
        return date_str

    app.jinja_env.globals.update(get_completed_date=get_completed_date)  

    def get_all_participants(session_id):
        all = db.session.query(Completed).filter(Completed.id_session == session_id).count()
        return all

    app.jinja_env.globals.update(get_all_participants=get_all_participants)  

    #function to solve problem to round even numbers
    def my_round(x):
        return int(x + math.copysign(0.5, x))

    def get_age_range(session_id):
        all_age = db.session.query(
                Detail.age
            ).filter(
                Completed.id_session==session_id,
            ).filter(
                User.id == Completed.id_user,
            ).filter(
                Detail.id_user==User.id
            ).all()
        
        age_range =[]
        for age in all_age:
            age_range.append(age[0])
            
        average = my_round(sum(age_range)/len(age_range))
        return [min(age_range),max(age_range),average]
    
    app.jinja_env.globals.update(get_age_range=get_age_range)

    def get_valuations(video_id):
        values = Valuation.query.filter_by(id_video=video_id).order_by(Valuation.id_user).all()
        return values

    app.jinja_env.globals.update(get_valuations=get_valuations)  

    return app

