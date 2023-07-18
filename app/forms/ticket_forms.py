from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, StringField, FloatField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed


class TicketPurchaseForm(FlaskForm):
    ticket_type_id = SelectField(
        "Ticket Type", coerce=int, id="ticketTypeSelet", validators=[DataRequired()]
    )
    quantity = IntegerField(
        "Number of Tickets",
        id="quantity",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="You must purchase at least one ticket"),
        ],
    )
    amount = StringField("Total Amount", id="amout", render_kw={"readonly": True})
    submit = SubmitField("Pusrchase")


class TicketTypeForm(FlaskForm):
    ticket_name = StringField("Ticket Name", validators=[DataRequired()])
    ticket_type = StringField("Ticket Type", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField(
        "Status",
        choices=[
            ("available", "available"),
            ("sold", "sold"),
            ("canceled", "canceled"),
        ],
        validators=[DataRequired()],
    )
    image = FileField(
        "Image", validators=[FileAllowed(["jpg", "jpeg", "gif", "webp", "png", "tif"])]
    )
    submit = SubmitField("Create Ticket Type")
