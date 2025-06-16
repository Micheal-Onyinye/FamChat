
from flask import Flask
from dotenv import load_dotenv
import os
from os import path
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = 'database.db'

def define_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///../{DB_NAME}'
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    db.init_app(app)

    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Group  # register models
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

# ✅ Keep setup_general_chat here, but don't run it inside define_app
def setup_general_chat():
    from .models import Group, User
    if not Group.query.filter_by(name="General Chat").first():
        general_group = Group(
            name="General Chat",
            description="Default group for everyone",
            profile_pic="avatar.jpg"  # Optional default
            # No creator_id needed here
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
            print('✅ Created database')
    else:
        print('✅ Database already exists')
