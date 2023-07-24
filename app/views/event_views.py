import os
from flask import redirect, render_template, flash, url_for, Blueprint, abort, request
from app.forms.event_forms import EventForm, CategoryForm
from app.models.models import Event, Category, User, db
from flask_login import current_user, login_required
from app.utills.utills import image_saver
from sqlalchemy.orm.exc import NoResultFound

event_bp = Blueprint("events", __name__)


@event_bp.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        # Save image and get image name
        image_name = image_saver(form.image.data, folder="event_pics")

        category_name = form.category.data
        category = Category.query.filter_by(category_name=category_name).first()

        if category is None:
            # Populate the category table with a new category
            category = Category(category_name=category_name)
            db.session.add(category)
            db.session.commit()

        event = Event(
            event_name=form.event_name.data,
            description=form.description.data,
            image=image_name,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            venue=form.venue.data,
            capacity=form.capacity.data,
            price=form.price.data,
            organizers=[current_user],
            category_id=category.id,
        )
        db.session.add(event)
        db.session.commit()

        flash("Congratulations! Your event has been created", "success")
        return redirect(url_for("events.event_detail", event_id=event.id))

    return render_template("event/create_event.html", title="New Event", form=form)


@event_bp.route("/add_category", methods=["GET", "POST"])
@login_required
def add_category():
    """This function is responsible for adding a new category to the system.
    It uses the CategoryForm to collect the category data, and upon validation,
    it saves the category in the database and redirects the user to the event creation page.
    """
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(category_name=form.category_name.data)
        db.session.add(category)
        db.session.commit()
        flash("Category added successfully.", "success")
        return redirect(url_for("events.create_event"))
    return render_template("event/add_category.html", form=form, title="Add Category")


@event_bp.route("/event/<int:event_id>")
def event_detail(event_id):
    """This function is responsible for displaying the details of a specific event.
    It accepts an event ID as a parameter and uses it to fetch and display the event's details.
    """
    event = Event.query.get_or_404(event_id)
    return render_template(
        "event/event_detail.html", event=event, title=event.event_name
    )


@event_bp.route("/event/<int:event_id>/update", methods=["GET", "POST"])
@login_required
def update_event(event_id):
    """This function is responsible for updating an existing event.
    It accepts an event ID as a parameter, fetches the event from the database,
    and updates its data based on the EventForm inputs."""
    event = Event.query.get_or_404(event_id)

    if event.organizers[0].id != current_user.id:
        abort(403)

    form = EventForm()

    if form.validate_on_submit():
        # Get the category
        category_name = form.category.data
        category = Category.query.filter_by(category_name=category_name).first()

        if category is None:
            # Populate the category table with a new category
            category = Category(category_name=category_name)
            db.session.add(category)
            db.session.commit()
        new_image = form.image.data
        if new_image is None:
            new_image = event.image
        else:
            if os.path.isfile(event.image):
                os.remove(event.image)

            new_image = image_saver(new_image, folder="event_pics")
        event.image = new_image
        event.event_name = form.event_name.data
        event.description = form.description.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.venue = form.venue.data
        event.capacity = form.capacity.data
        event.price = form.price.data

        event.category_id = category.id
        db.session.commit()
        flash("Your event has been Updated!", "success")
        return redirect(url_for("events.event_detail", event_id=event.id))

    elif request.method == "GET":
        form.event_name.data = event.event_name
        form.description.data = event.description
        form.start_date.data = event.start_date
        form.end_date.data = event.end_date
        form.start_time.data = event.start_time
        form.end_time.data = event.end_time
        form.venue.data = event.venue
        form.capacity.data = event.capacity
        form.price.data = event.price
        # Here we use the category name, not the ID
        form.category.data = event.category.category_name

    return render_template("event/create_event.html", title="Update Event", form=form)


@event_bp.route("/event/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id):
    """This function is responsible for deleting an event.
    It accepts an event ID as a parameter, fetches the event from the database, and deletes it.
    The function ensures that the user attempting to delete the event is the event organizer.
    """
    event = Event.query.get_or_404(event_id)
    if event.organizers[0].id != current_user.id:
        abort(403)
    db.session.delete(event)
    db.session.commit()
    flash("Your event has been deleted!", "success")
    return redirect(url_for("user.home"))


# Event list view
@event_bp.route("/events")
@login_required
def list_events():
    """This function is responsible for listing all the events in the system.
    It fetches all events from the database and displays them to the user."""
    events = Event.query.all()
    return render_template("event/event_list.html", events=events, title="Events List")


@event_bp.route("/event/user/<string:username>")
def user_events(username):
    """This function is responsible for listing all the events organized by a specific user.
    It accepts a username as a parameter, fetches the user's events from the database, and displays them to the user.
    """

    # Get the user by username or return 404 if not found
    user = User.query.filter_by(username=username).first_or_404()

    # Query all events organized by the user
    events = (
        Event.query.filter(Event.organizers.contains(user))
        .order_by(Event.created_at.desc())
        .all()
    )

    # Render the user's events page
    return render_template(
        "event/user_events.html",
        events=events,
        title=f"{user.username}'s Events",
        user=user,
    )
