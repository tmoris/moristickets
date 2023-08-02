from flask import (
    redirect,
    render_template,
    flash,
    url_for,
    session,
    request,
    Blueprint,
)
from app.forms.user_forms import (
    SignupForm,
    LoginForm,
    UpdateAccountForm,
    TestimonialForm,
    ContactForm,
)
from app.forms.event_forms import EventForm
from app.models.models import User, Event, Testimonial, Ticket, Contact
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from werkzeug.urls import url_parse
from app.utills.utills import image_saver, process_contact_form


user_bp = Blueprint("user", __name__)


# Create contact_api
@user_bp.route("/api/contact", methods=["POST"])
def contact_api():
    contact_form = ContactForm()
    return process_contact_form(contact_form)


@user_bp.route("/", methods=["GET", "POST"])
def homepage():
    contact_form = ContactForm()
    page = request.args.get("page", 1, type=int)
    events = Event.query.order_by(Event.created_at.desc()).paginate(
        page=page, per_page=6
    )
    testimonials = Testimonial.query.all()
    tickets = Ticket.query.all()

    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        # Extracting data from the form and processing
        name = contact_form.name.data
        email = contact_form.email.data
        message = contact_form.message.data

        # Creating a new Contact object and adding it to the database
        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("user.homepage"))

    return render_template(
        "index.html",
        events=events,
        contact_form=contact_form,
        testimonials=testimonials,
        tickets=tickets,
        title="Landing page",
    )


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash("Invalid email address", "danger")
            return render_template("user/login.html", title="Sign In", form=form)
        if not user.check_password(form.password.data):
            flash("Invalid password", "danger")
            return render_template("user/login.html", title="Sign In", form=form)
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("user.home")
        return redirect(next_page)
    return render_template("user/login.html", title="Sign In", form=form)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You are already registered and logged in!", "info")
        return redirect(url_for("user.home"))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
        )
        user.hash_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, You are now a registered!", "success")
        return redirect(url_for("user.login"))

    return render_template("user/register.html", form=form, title="Sing up")


@user_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sorry to see you Go!", "info")
    return redirect(url_for("user.homepage"))


@user_bp.route("/home", methods=["GET", "POST"])
@login_required
def home():
    events = Event.query.all()
    return render_template("user/home.html", title="User Home", events=events)


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    updated = session.pop("updated", False)
    return render_template(
        "user/user_profile.html", title="User Profile", updated=updated
    )


@user_bp.route("/profile/update", methods=["GET", "POST"])
@login_required
def account_update():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.profile_pic.data:
            profile_image = image_saver(form.profile_pic.data, folder="profile_pics")
        else:
            profile_image = current_user.profile_pic
        if form.company_logo.data:
            logo = image_saver(form.company_logo.data, folder="company_logos")
            current_user.company_logo = logo

        current_user.profile_pic = profile_image
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        current_user.address = form.address.data
        current_user.phone_number = form.phone_number.data
        current_user.company_name = form.company_name.data
        db.session.commit()
        flash("Your account info has been updated successfully", "success")
        return redirect(url_for("user.profile"))
    if request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.address.data = current_user.address
        form.phone_number.data = current_user.phone_number
        form.company_name.data = current_user.company_name
    profile_pic = (
        url_for("static", filename="img/profile_pics/" + current_user.profile_pic)
        if current_user.profile_pic
        else None
    )
    company_logo = (
        url_for("static", filename="img/company_logos/" + current_user.company_logo)
        if current_user.company_logo
        else None
    )

    return render_template(
        "user/user_profile.html",
        form=form,
        title=f"{current_user.username}'s Account Update",
        profile_image=profile_pic,
        company_logo=company_logo,
    )


@user_bp.route("/add_testimonial", methods=["GET", "POST"])
def add_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            testimony=form.testimony.data,
            author_id=current_user.id,
            author_role=form.role.data,
        )
        db.session.add(testimonial)
        db.session.commit()
        flash("Your testimony has been added successfuly!", "success")
        return redirect(url_for("user.home"))
    return render_template(
        "user/add_testimonial.html", form=form, title="Talk about us"
    )


@user_bp.route("/about", methods=["GET", "POST"])
def about():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        # Extracting data from the form and processing
        name = contact_form.name.data
        email = contact_form.email.data
        message = contact_form.message.data

        # Creating a new Contact object and adding it to the database
        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("user.about"))
    return render_template("about.html", contact_form=contact_form)


@user_bp.route("/pricing")
def pricing():
    return render_template("pricing.html")
