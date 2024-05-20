from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager


db = SQLAlchemy(session_options={"autoflush": False})
# DB_NAME = "matchingbusiness.db"
DB_NAME_MYSQL = "thesis"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'th3s1s_s0urce'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:Andyzxc4@localhost/{DB_NAME_MYSQL}"
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Educator, Coordinator
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        # Try to load the user from the Educator table
        user = Educator.query.get(int(id))
        if user:
            return user
        # If not found in the Educator table, try loading from the Coordinator table
        user = Coordinator.query.get(int(id))
        return user

    return app


