from flask import (
    redirect,
    render_template,
    flash,
    url_for,
    session,
    request,
    Blueprint,
)
from app.forms.user_forms import SignupForm, LoginForm, UpdateAccountForm
from app.models.models import User, Event
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from werkzeug.urls import url_parse
from app.utills.utills import image_saver


user_bp = Blueprint("user", __name__)


@user_bp.route("/", methods=["GET", "POST"])
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


@user_bp.route("/regiseter", methods=["GET", "POST"])
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
    flash("Sorry to see you! logout!", "info")
    return redirect(url_for("user.login"))


@user_bp.route("/home", methods=["GET", "POST"])
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

        current_user.profile_pic = profile_image
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash("Your account info has been updated successfully", "success")
        return redirect(url_for("user.profile"))
    if request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    return render_template(
        "user/user_profile.html",
        form=form,
        title=f"{current_user.username}'s Account Update",
    )
