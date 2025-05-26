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

    from .models import User
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

def create_database(app): 
  DB_NAME = "database.db" # Define DB_NAME here as well, inside the function
  if not path.exists(f'APP/{DB_NAME}'):
        with app.app_context():
            db.create_all()
            print('Created database')
