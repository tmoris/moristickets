import os
import qrcode
import tempfile
import pdfkit
from flask import (
    redirect,
    render_template,
    url_for,
    flash,
    Blueprint,
    request,
    send_file,
    current_app,
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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import inch


ticket_bp = Blueprint("ticket", __name__)


@ticket_bp.route("/event/<int:event_id>/purchase", methods=["GET", "POST"])
@login_required
def purchase_ticket(event_id):
    event = Event.query.get_or_404(event_id)

    # Initialize a ticket purchase form
    form = TicketPurchaseForm()

    # Get all ticket types for the given event
    form.ticket_type_id.choices = [(t.id, t.ticket_type) for t in event.ticket_types]

    if form.validate_on_submit():
        # Fetch ticket type from the database
        ticket_type = TicketType.query.get_or_404(form.ticket_type_id.data)

        # check ticket type exists and if there are tickets available
        if (
            not ticket_type
            and ticket_type.status != "available"
            and ticket_type.quantity < form.quantity.data
        ):
            flash(
                "Purchase unsuccessful. The ticket type is not available or sold out ",
                "danger",
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
        balance = 1000
        if balance < total_amount:
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
                use_status="unused",
            )
            db.session.add(new_ticket)

        # Decrease the ticket type quantity
        ticket_type.quantity -= form.quantity.data
        if ticket_type.quantity == 0:
            ticket_type.status = "sold"

        # deduct user balance
        balance -= total_amount

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
        f"Ticket ID: {ticket.id}\nUser ID: {current_user.id}\nEvent ID: {ticket.ticket_type.event.id}\nTicket Type ID: {ticket.ticket_type.id}\nPurchase Date/Time: {ticket.purchase_date}\nTicket Status: {ticket.use_status}"
    )
    qr_code_image = qr.make_image(fill="black", back_color="white")

    # Convert QR Code image to PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Fetch the built-in styles
    styles = getSampleStyleSheet()

    # Build the PDF Elements
    elements = []
    if ticket.ticket_type.image is not None:
        # Add company logo
        logo_path = os.path.join(
            current_app.root_path,
            "static",
            "img",
            "ticket_pics",
            ticket.ticket_type.image,
        )
    else:
        # Add company logo
        logo_path = os.path.join(
            current_app.root_path,
            "static",
            "img",
            "event_pics",
            ticket.ticket_type.event.image,
        )

    logo = Image(logo_path, width=4 * inch, height=3 * inch)
    elements.append(logo)
    elements.append(Spacer(1, 0.25 * inch))

    styles = getSampleStyleSheet()
    # Add a Justified style
    styles.add(
        ParagraphStyle(
            name="Justify",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
            leftIndent=85,
            rightIndent=15,
        )
    )
    # Add Ticket Information
    elements.append(Paragraph(f"User: {current_user.username}", styles["Justify"]))
    elements.append(
        Paragraph(
            f"Event Name: {ticket.ticket_type.event.event_name}", styles["Justify"]
        )
    )
    elements.append(
        Paragraph(f"Event ID: {ticket.ticket_type.event.id}", styles["Justify"])
    )
    elements.append(
        Paragraph(f"Ticket Type ID: {ticket.ticket_type.id}", styles["Justify"])
    )
    elements.append(
        Paragraph(
            f"Purchase Date/Time: {ticket.purchase_date.strftime('%B %d, %Y, %I:%M %p')}",
            styles["Justify"],
        )
    )
    elements.append(
        Paragraph(
            f"Ticket Price: ${ticket.ticket_type.price}",
            styles["Justify"],
        )
    )
    elements.append(Paragraph(f"Ticket Status: {ticket.use_status}", styles["Justify"]))
    # save the qr_code_image to a temperary file
    fp = tempfile.TemporaryFile(suffix=".png")
    qr_code_image.save(fp, "PNG")
    fp.seek(0)

    # Add QR code image
    img = Image(fp, width=2 * inch, height=2 * inch)
    elements.append(img)

    # Generate PDF
    doc.build(elements)

    # Return the PDF file
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="ticket.pdf",
    )


@ticket_bp.route("/events/<int:event_id>/ticket_type/new", methods=["GET", "POST"])
@login_required
def new_ticket_type(event_id):
    event = Event.query.get_or_404(event_id)

    if current_user not in event.organizers:
        flash(
            "You do not have the necessary permissions to perform this action!",
            "danger",
        )
        return redirect(url_for("ticket.new_ticket_type"))

    form = TicketTypeForm()

    if form.validate_on_submit():
        try:
            existing_ticket_type = TicketType.query.filter_by(
                event_id=event.id, ticket_type=form.ticket_type.data
            ).first()

            if existing_ticket_type:
                flash(
                    "You have already created this ticket_type for this event.", "info"
                )
                return redirect(
                    url_for(
                        "ticket.ticket_type_detail",
                        ticket_type_id=existing_ticket_type.id,
                    )
                )

            else:
                image_file = image_saver(form.image.data, folder="ticket_pics")
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
                return redirect(
                    url_for("ticket.ticket_type_detail", ticket_id=ticket_type.id)
                )
        except Exception as e:
            db.session.rollback()
            flash(str(e), "error")

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
        return redirect(url_for("user.home"))

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
        return redirect(url_for("user.home"))

    # Update the ticket status (assuming new status is sent in 'status' field of POST data)
    new_status = request.form.get("status")
    ticket.status = new_status
    db.session.commit()

    flash("Ticket status updated successfully!", "success")
    return redirect(url_for("ticket.ticket_status", ticket_id=ticket.id))


@ticket_bp.route("/events/<int:event_id>/ticket_types", methods=["GET"])
def get_ticket_types(event_id):
    event = Event.query.get_or_404(event_id)
    ticket_types = event.ticket_types
    return render_template(
        "ticket/ticket_types.html",
        ticket_types=ticket_types,
        title=f"{event.event_name} Ticket_Types",
    )


@ticket_bp.route("/ticket_type/<int:ticket_type_id>", methods=["GET"])
@login_required
def ticket_type_detail(ticket_type_id):
    # Fetch the ticket by ID from the database
    ticket = TicketType.query.get_or_404(ticket_type_id)

    # Check if the current user is the owner of the ticket
    if current_user not in ticket.event.organizers:
        flash(
            "You do not have the necessary permissions to view this ticket!", "danger"
        )
        return redirect(url_for("user.home"))

    return render_template(
        "ticket/ticket_type_detail.html", ticket=ticket, ticket_type_id=ticket_type_id
    )


@ticket_bp.route("/users/<int:user_id>/tickets", methods=["GET"])
@login_required
def get_user_tickets(user_id):
    user = User.query.get_or_404(user_id)
    tickets = user.tickets
    return render_template(
        "ticket/user_tickets.html", tickets=tickets, title=f"{user.username}'s Tickets"
    )


@ticket_bp.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id:
        abort(401)  # Unauthorized
    db.session.delete(ticket)
    db.session.commit()
    flash("Your ticket has been deleted successfully!", "success")
    return redirect(url_for("ticket.get_user_tickets", user_id=ticket.user_id))


@ticket_bp.route("/tickets")
@login_required
def tickets():
    tickets = TicketType.query.all()
    return render_template("ticket/ticket_list.html", tickets=tickets, title="Tickets")
