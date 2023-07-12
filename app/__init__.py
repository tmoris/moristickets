from flask import Flask
from config import Config


def creat_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    return app
