import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class Config(object):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Basic Secret_key configurations
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = os.environ.get("DEBUG") or True
    # Database URl configurations
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
