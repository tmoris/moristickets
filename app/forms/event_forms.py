from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    DateField,
    TimeField,
    SelectMultipleField,
    IntegerField,
    FloatField,
    SelectField,
)
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileField, FileAllowed
from wtforms_components import DateRange
from wtforms.validators import NumberRange

from datetime import date


class EventForm(FlaskForm):
    """
    EventForm is a FlaskForm for creating an event. It has the following fields:
    event_name, description, image, start_date, end_date, start_time, end_time, venue, and a submit button.
    """

    event_name = StringField("Event Name", validators=[DataRequired()])

    description = TextAreaField("Description", validators=[DataRequired()])

    image = FileField(
        "Event Image",
        validators=[FileAllowed(["jpg", "jpeg", "gif", "webp", "png", "tif"])],
    )  #   image: A file field for the event's image. It only accepts certain file formats.

    start_date = DateField(
        "Start Date", validators=[DateRange(min=date.today()), DataRequired()]
    )
    end_date = DateField("End Date", validators=[DataRequired()])
    start_time = TimeField("Start Time", validators=[DataRequired()])
    end_time = TimeField("End Time", validators=[DataRequired()])
    venue = StringField("Venue", [DataRequired()])
    capacity = IntegerField("Capacity", validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField("Price", validators=[DataRequired()])
    category = StringField("Category", validators=[DataRequired()])
    submit = SubmitField("Create Event")

    def validate_end_date(form, field):
        """
        validate_end_date: A custom validator for end_date field. It ensures that the end_date is not earlier than the start_date.
        """
        if field.data < form.start_date.data:
            raise ValidationError("End data must not be earlier than start date.")


class CategoryForm(FlaskForm):
    category_name = StringField("Category Name", validators=[DataRequired()])
    submit = SubmitField("Add Category")
