from flask import Flask
from dotenv import load_dotenv
import os
from os import path
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO 

db = SQLAlchemy()
DB_NAME = 'database.db'
socketio = SocketIO() 

def define_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///../{DB_NAME}'
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    db.init_app(app)

    # Initialize SocketIO with the app instance
    socketio.init_app(app) 

    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Group # register models
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    
    import APP.views # <--- Ensures views are imported for SocketIO event discovery

    return app


def setup_general_chat():
    from .models import Group, User
    if not Group.query.filter_by(name="General Chat").first():
        general_group = Group(
            name="General Chat",
            description="Default group for everyone",
            profile_pic="avatar.jpg" 
            
        )
        db.session.add(general_group)
        db.session.commit()

    group = Group.query.filter_by(name="General Chat").first()
    if group:
        users = User.query.all()
        for user in users:
            if user not in group.members:
                group.members.append(user)
        db.session.commit()


def create_database(app):
    if not path.exists(f'APP/{DB_NAME}'):
        with app.app_context():
            db.create_all()
            print(' Created database')
    else:
        print(' Database already exists')
