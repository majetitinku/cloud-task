from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    # already logged in? just send them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        # quick check, nothing fancy
        if not username or not email or not password:
            flash("Please fill all fields", "danger")
            return redirect(url_for("auth.register"))

        # check if user exists already
        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            flash("Username or email already exists", "warning")
            return redirect(url_for("auth.register"))

        # create user
        user = User(username=username, email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        current_app.logger.info("new account: %s", username)

        flash("Registered successfully, login now", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        # basic auth check
        if user and user.check_password(password):
            login_user(user)

            current_app.logger.info("login ok: %s", user.username)

            flash("Welcome back", "success")
            return redirect(url_for("main.dashboard"))

        # failed login
        current_app.logger.info("login failed: %s", username)
        flash("Wrong username or password", "danger")

        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    current_app.logger.info("user logout: %s", current_user.username)

    logout_user()

    flash("Logged out", "info")
    return redirect(url_for("auth.login"))