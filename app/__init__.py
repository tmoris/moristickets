from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "user.login"
login_manager.login_message = (
    "The page you requested requires you to login first, Please log in to access page!"
)
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Database initialization
    db.init_app(app)

    # Login manager Initiallization
    login_manager.init_app(app)
    from app.models.user_model import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Database creating context
    with app.app_context():
        db.create_all()

    return app
