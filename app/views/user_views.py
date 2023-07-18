from flask import (
    redirect,
    render_template,
    flash,
    url_for,
    session,
    request,
    Blueprint,
)
from app.forms.user_forms import SignupForm, LoginForm
from app.models.models import User, Event
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from werkzeug.urls import url_parse


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
        flash("Congratulations, You are now a registered!", "Success")
        return redirect(url_for("user.login"))

    return render_template("user/register.html", form=form, title="Sing up")


@user_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sorry to see you! logout!")
    return redirect(url_for("user.login"))


@user_bp.route("/home", methods=["GET", "POST"])
def home():
    events = Event.query.all()
    return render_template("user/home.html", title="User Home", events=events)


@user_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("user/dashboard.html", title="Dashboard")
