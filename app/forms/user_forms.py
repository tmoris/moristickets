from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    EmailField,
    PasswordField,
    SubmitField,
    BooleanField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from app.models.models import User
from flask_wtf.file import FileAllowed, FileField


class SignupForm(FlaskForm):
    """
    This class represents a form for user registration.
    It contains basic fields required for user to register, including validation rule.
    The 'Confim_password field is used to ensure users type in the password correctly'
    """

    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        """Function to check if username already exists in the database

        Raise a validation error if username exists
        Args: username (str): username to be checked
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "Username is already taken,Choose another name please!"
            )

    def validate_email(self, email):
        """
        Function to check if email already exists in the database
         Raise a validation error if email exists
        Args: email (str): email to be checked
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Email already in user.!")


class LoginForm(FlaskForm):
    """This class represents a form for user login.
    It includes basic fields required for a user to log in to their account"""

    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me", validators=[Optional()])
    submit = SubmitField("Log In")


class UpdateAccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    profile_pic = FileField(
        "Upload profile picture",
        validators=[FileAllowed(["jpg", "jpeg", "gif", "webp", "png", "tif"])],
    )
    bio = TextAreaField("About You (Biography)")
    address = StringField("Address", validators=[Optional()])
    phone_number = StringField("Phone Number", validators=[Optional()])
    company_name = StringField("Company Name", validators=[Optional()])
    company_logo = FileField(
        "Upload Company Logo",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp", "tif"])],
    )
    submit = SubmitField("Update Profile")


class TestimonialForm(FlaskForm):
    """
    This class represents a form for submitting a testimonial.
    It requires the testimonial content and the author's role.
    """

    # Form to submit a testimonial
    testimony = TextAreaField("Testimony", validators=[DataRequired()])
    role = StringField("Author's Role", validators=[DataRequired()])
    submit = SubmitField("Submit")


class ContactForm(FlaskForm):
    """
    This class represents a form for sending a contact message.
    It requires fields for the user's name, email, and the message they wish to send.
    """

    # Form to allow a user to send a contact message
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")
