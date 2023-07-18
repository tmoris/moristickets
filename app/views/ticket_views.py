import qrcode
from flask import (
    redirect,
    render_template,
    url_for,
    flash,
    Blueprint,
    request,
    send_file,
    abort,
)
from flask_login import current_user, login_required
from app.models.models import Event, Ticket, TicketType, User, db
from datetime import datetime
from app.forms.ticket_forms import TicketPurchaseForm, TicketTypeForm
from app.utills.utills import image_saver
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


ticket_bp = Blueprint("ticket", __name__)


@ticket_bp.route("/event/<int:event_id>/purchase", methods=["GET", "POST"])
@login_required
def purchase_ticket(event_id):
    event = Event.query.get_or_404(event_id)

    # Initialize a ticket purchase form
    form = TicketPurchaseForm()

    # Get all ticket types for the given event
    form.ticket_type_id.choices = [(t.id, t.ticket_name) for t in event.ticket_types]

    if form.validate_on_submit():
        ticket_type = TicketType.query.get(form.ticket_type_id.data)

        # Fetch ticket type from the database
        ticket_type = TicketType.query.get_or_404(form.ticket_type_id.data)

        # check ticket type exists and if there are tickets available
        if (
            ticket_type
            and ticket_type.status == "available"
            and ticket_type.quantity >= form.quantity.data
        ):
            flash(
                "Purchase unsuccessful. The ticket type is not available or sold out "
            )
            return render_template(
                "ticket/purchase_ticket.html",
                title="Purchase Ticket",
                form=form,
                event=event,
            )

        #  check if user has enough balance to purchase the ticket
        user = User.query.get(current_user.id)
        total_amount = ticket_type.price * form.quantity.data
        if user.balance < total_amount:
            flash("Purchase unsuccessful. Insufficient funds ")
            return render_template(
                "ticket/purchase_ticket.html",
                title="Purchase Ticket",
                form=form,
                event=event,
            )

        # Create and store tickets in the database
        for _ in range(form.quantity.data):
            new_ticket = Ticket(
                user_id=current_user.id,
                ticket_type_id=ticket_type.id,
                purchase_date=datetime.utcnow(),
                status="unused",
            )
            db.session.add(new_ticket)

        # Decrease the ticket type quantity
        ticket_type.quantity -= form.quantity.data
        if ticket_type.quantity == 0:
            ticket_type.status = "sold"

        # deduct user balance
        user.balance -= total_amount

        # Save changes to database
        db.session.commit()

        flash(
            f"Ticket purchase successful! {form.quantity.data} tickets bought. ticket_id: {new_ticket.id}",
            "success",
        )
        return redirect(url_for("ticket.download_ticket", ticket_id=new_ticket.id))

    return render_template(
        "ticket/purchase_ticket.html", form=form, event=event, title="Purchase Ticket"
    )


@ticket_bp.route("/download_ticket/<int:ticket_id>", methods=["GET"])
@login_required
def download_ticket(ticket_id):
    # Retrieve the ticket
    ticket = Ticket.query.get_or_404(ticket_id)

    # Validate that the current user is the owner of the ticket
    if current_user != ticket.user:
        flash(
            "You do not have the necessary permissions to perform this action!",
            "danger",
        )
        return redirect(url_for("user.home"))

    # Create a QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(
        f"Ticket ID: {ticket.id}\nUser ID: {current_user.id}\nEvent ID: {ticket.event.id}\nTicket Type ID: {ticket.ticket_type.id}\nPurchase Date/Time: {ticket.purchase_date}\nTicket Status: {ticket.status}"
    )
    qr_code_image = qr.make_image(fill="black", back_color="white")

    # Convert QR Code image to PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Fetch the built-in styles
    styles = getSampleStyleSheet()

    # Build the PDF Elements
    elements = []

    # Add company logo
    logo_path = ""
    logo = Image(logo_path, width=2 * inch, height=2 * inch)
    elements.append(logo)
    elements.append(Spacer(1, 0.25 * inch))

    # Add Ticket Information
    elements.append(Paragraph(f"User: {current_user.username}", styles["Normal"]))
    elements.append(Paragraph(f"Event ID: {ticket.event.id}", styles["Normal"]))
    elements.append(
        Paragraph(f"Ticket Type ID: {ticket.ticket_type.id}", styles["Normal"])
    )
    elements.append(
        Paragraph(f"Purchase Date/Time: {ticket.purchase_date}", styles["Normal"])
    )
    elements.append(Paragraph(f"Ticket Status: {ticket.status}", styles["Normal"]))

    # Add QR code image
    img = Image(qr_code_image, width=2 * inch, height=2 * inch)
    elements.append(img)

    # Generate PDF
    doc.build(elements)

    # Return the PDF file
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        attachment_filename="ticket.pdf",
        mimetype="application/pdf",
    )


@ticket_bp.route("/events/<int:event_id>/ticket_type/new", methods=["GET", "POST"])
@login_required
def new_ticket_type(event_id):
    event = Event.query.get_or_404(event_id)

    #  If the current user is not the event organizer
    if current_user not in event.organizers:
        flash(
            "You do not have the necessary permissions to perform this action!",
            "danger",
        )
        return redirect(url_for("ticket.new_ticket_type"))

    # Initialize the ticket type form
    form = TicketTypeForm()

    # Check if a ticket already exists for this event by the current user
    if form.validate_on_submit():
        existing_ticket_type = TicketType.query.filter_by(
            event_id=event.id, ticket_type=form.ticket_type.data
        ).first()
        if existing_ticket_type:
            flash("You have already created this ticket_type for this event.", "info")
            return redirect(url_for("ticket.list_tickets"))

        # get image_file and save
        image_file = image_saver(form.image.data, folder="ticket_pics")

        # Create a new Ticket object with the form data
        ticket_type = TicketType(
            ticket_name=form.ticket_name.data,
            ticket_type=form.ticket_type.data,
            price=form.price.data,
            quantity=form.quantity.data,
            status=form.status.data,
            image=image_file,
            event_id=event.id,
        )
        db.session.add(ticket_type)
        db.session.commit()
        flash("The ticket type has been created!", "success")
        return redirect(url_for("ticket.ticket_type_detail", event_id=event.id))

    return render_template(
        "ticket/create_ticket_type.html",
        title="New Ticket Type",
        form=form,
        legend="New Ticket Type",
    )


@ticket_bp.route("/ticket_status/<int:ticket_id>", methods=["GET"])
@login_required
def ticket_status(ticket_id):
    # Retrieve the ticket
    ticket = Ticket.query.get_or_404(ticket_id)

    # Validate that the current user is the owner of the ticket
    if current_user != ticket.user:
        flash(
            "You do not have the necessary permissions to perform this action!",
            "danger",
        )
        return redirect(url_for("main.home"))

    # Return the ticket status
    return render_template("ticket/status.html", ticket=ticket)


@ticket_bp.route("/update_ticket_status/<int:ticket_id>", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    # Retrieve the ticket
    ticket = Ticket.query.get_or_404(ticket_id)

    # Validate that the current user is the owner of the ticket
    if current_user != ticket.user:
        flash(
            "You do not have the necessary permissions to perform this action!",
            "danger",
        )
        return redirect(url_for("main.home"))

    # Update the ticket status (assuming new status is sent in 'status' field of POST data)
    new_status = request.form.get("status")
    ticket.status = new_status
    db.session.commit()

    flash("Ticket status updated successfully!", "success")
    return redirect(url_for("ticket.ticket_status", ticket_id=ticket.id))


@ticket_bp.route("/list_tickets/<int:user_id>", methods=["GET"])
@login_required
def list_tickets(user_id):
    # Validate that the current user is the one whose tickets are being listed
    if current_user.id != user_id:
        flash(
            "You do not have the necessary permissions to perform this action!",
            "danger",
        )
        return redirect(url_for("user.home"))

    # Retrieve the tickets
    tickets = Ticket.query.filter_by(user_id=user_id).all()

    return render_template("ticket/list.html", tickets=tickets)
