from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from functools import wraps
import logging

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


class _QuietPolling(logging.Filter):
    """Hide the many "GET /group/<id>/state" lines; printing them to the Windows
    console slows the app down while testers type."""

    def filter(self, record):
        message = record.getMessage()
        return '/state' not in message


# Columns added after the first release: table -> [(column, SQL type)].
# create_all() only creates missing tables, so old databases get them here.
_NEW_COLUMNS = {
    'tester': [('name', 'VARCHAR(100)'),
               ('batch', 'INTEGER NOT NULL DEFAULT 1'),
               ('started', 'DATETIME')],
    'group_run': [('batch', 'INTEGER NOT NULL DEFAULT 1')],
    'session': [('created', 'DATETIME')],
}


def _upgrade_schema():
    """Add columns that create_all() cannot add to an existing database."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    for table, new_columns in _NEW_COLUMNS.items():
        if table not in tables:
            continue
        existing = {column['name'] for column in inspector.get_columns(table)}
        for column, sql_type in new_columns:
            if column not in existing:
                with db.engine.begin() as connection:
                    connection.execute(text(
                        f'ALTER TABLE "{table}" ADD COLUMN {column} {sql_type}'))


def create_app():
    app = Flask(__name__)  # inicialize Flask
    werkzeug_log = logging.getLogger('werkzeug')
    if not any(isinstance(item, _QuietPolling) for item in werkzeug_log.filters):
        werkzeug_log.addFilter(_QuietPolling())
    app.config['SECRET_KEY'] = 'fsYdgSF*GG5fd'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.config['REMEMBER_COOKIE_DURATION'] = 3600

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .admin import admin
    from .group import group
    from .models import (User, Session, Sequence, Video, Training,
                         GroupRun, Tester, GroupVote)

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(group, url_prefix='/group')

    with app.app_context():
        db.create_all()
        _upgrade_schema()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))  # pre primary key

    def get_user_name(user_id):
        user = User.query.filter_by(id=user_id).first()
        return user.username if user else 'Unknown User'

    app.jinja_env.globals.update(get_user_name=get_user_name)

    return app
