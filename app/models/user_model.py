from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """
    Model representing a user. Each user has a unique username and email.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    profile_pic = db.Column(db.String(128), default="default.jpg")
    bio = db.Column(db.Text)

    def hash_password(self, password):
        """
        Generates a hashed version of the given password and stores it.
        Args:
        password (str): The password to hash and store.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks wether the given password matches the stored hashed password
        Args:
        password (str): The password to check
        """
        return check_password_hash(self.password_hash, password)
