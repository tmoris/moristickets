from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Enum

db = SQLAlchemy()


class Role(db.Model):
    """
    The Role model represents a user role in the database.

    Roles could be utilized for managing user permissions, such as determining which
    users are able to create events, manage events, or perform administrative functions.

    Attributes:
    - id: unique identifier
    - role_name: the name of the role, which cannot be null and must be unique
    - users: users that have this role

    The 'users' attribute establishes a one-to-many relationship from Role to User model,
    which means one role can be associated with many users. You can access a user's role
    through the 'role' attribute and a role's associated users through the 'users' attribute.
    """

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True)
    users = db.relationship("User", backref="role", lazy="dynamic")


organizers = db.Table(
    "organizers",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("event_id", db.Integer, db.ForeignKey("event.id"), primary_key=True),
)


class Event(db.Model):
    """
    The Event model represents an event in the database.

    Attributes:
    - id: unique identifier
    - event_name: name of the event, which cannot be null
    - description: description of the event, which cannot be null
    - image: image associated with the event, defaults to 'default.jpg'
    - created_at: date and time when the event was created, defaults to the current date and time
    - start_date: start date of the event, which cannot be null
    - end_date: end date of the event, which cannot be null
    - start_time: start time of the event, which cannot be null
    - end_time: end time of the event, which cannot be null
    - venue: venue of the event, which cannot be null
    - organizers: users who organize the event
    - category_id: foreign key to Category model, represents the category of the event

    There are check constraints to ensure that start_date is not in the past and that end_date is not before start_date.
    """

    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image = db.Column(db.String(128), nullable=False, default="default.jpg")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Integer, nullable="False")
    price = db.Column(db.Float, nullable=False)
    organizers = db.relationship(
        "User", secondary=organizers, backref=db.backref("events", lazy="dynamic")
    )
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    ticket_types = db.relationship(
        "TicketType", back_populates="event", overlaps="ticket_types,ticket_types"
    )

    __table_args__ = (
        CheckConstraint("start_date >= CURRENT_DATE", name="start_date_future_check"),
        CheckConstraint(
            "end_date >= start_date", name="end_date_after_start_date_check"
        ),
    )


class User(UserMixin, db.Model):
    """
    The User model represents a user in the database. It inherits from the Flask-Login UserMixin,
    which provides default implementations for properties and methods that Flask-Login expects a
    user object to have.

    Attributes:
    - id: unique identifier
    - username: username, which is unique and cannot be null
    - email: user's email address, which is unique and cannot be null
    - password_hash: hashed password, used for security
    - profile_pic: user's profile picture, defaults to 'default.jpg'
    - bio: user's short self-description

    Methods:
    - hash_password(password): Generates a hashed version of the given password and stores it.
    - check_password(password): Checks whether the given password matches the stored hashed password.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    profile_pic = db.Column(db.String(128), default="default.jpg")
    bio = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))

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


class TicketType(db.Model):
    """
    The TicketType class is a database model that represents types of tickets that an event can have.

    It has the following attributes:
    - id: unique identifier
    - ticket_name: name of the ticket
    - ticket_type: a string representing the type of ticket (ordinary, VIP, etc.)
    - price: price of the ticket
    - quantity: total quantity of the type of ticket
    - status: status of the ticket, can be 'available', 'sold', 'canceled'
    - image: image associated with the ticket
    - event_id: foreign key to Event model, represents the event to which the ticket is associated

    The Event relationship establishes a one-to-many relationship with the TicketType model with
    the 'event' backref, allowing access from the Event to its associated tickets.
    """

    id = db.Column(db.Integer, primary_key=True)
    ticket_name = db.Column(db.String(128), nullable=False)
    ticket_type = db.Column(db.String(120), nullable=False, default="Ordinary")
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(
        Enum("available", "sold", "canceled"), nullable=False, default="available"
    )
    image = db.Column(db.String(120), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    event = db.relationship(
        "Event", back_populates="ticket_types", overlaps="ticket_types,ticket_types"
    )

    def __repr__(self):
        return f"TicketType('{self.ticket_name}', '{self.ticket_type}', '{self.price}', '{self.quantity}', '{self.status}')"


class Ticket(db.Model):
    """
    The Ticket class is a database model that represents a ticket bought by a user.

    It has the following attributes:
    - id: unique identifier
    - user_id: foreign key to User model, represents the user who bought the ticket
    - ticket_type_id: foreign key to TicketType model, represents the type of ticket bought
    - purchase_date: the date the ticket was purchased
    - status: status of the ticket, can be 'unused', 'used', 'cancelled'

    The User and TicketType relationships establish one-to-many relationships with the Ticket model,
    allowing access from the User and TicketType to their associated tickets.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ticket_type_id = db.Column(
        db.Integer, db.ForeignKey("ticket_type.id"), nullable=False
    )
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    use_status = db.Column(
        Enum("unused", "used", "cancelled"), nullable=True, default="unused"
    )
    user = db.relationship(
        "User", backref=db.backref("tickets", cascade="all, delete-orphan")
    )
    ticket_type = db.relationship(
        "TicketType", backref=db.backref("tickets", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"Ticket('{self.id}','{self.status}', owned by User'{self.user_id}' )"


class Category(db.Model):
    """
    The Category model represents a category of events in the database.

    Attributes:
    - id: unique identifier
    - category_name: name of the category, which cannot be null and must be unique
    - events: events that belong to this category
    """

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(128), unique=True, nullable=False)
    events = db.relationship("Event", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"Category('{self.category_name}')"
