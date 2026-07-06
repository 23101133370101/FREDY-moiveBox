from datetime import datetime
from urllib.parse import urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from database import db
from models.user import User
from models.login_attempt import LoginAttempt

auth_bp = Blueprint("auth", __name__)


def _is_safe_next(target):
    return target and not urlparse(target).netloc and target.startswith("/")


class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("movies.index"))

    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("An account with that email already exists.", "danger")
            return render_template("signup.html", form=form)

        if User.query.filter_by(username=form.username.data).first():
            flash("That username is taken.", "danger")
            return render_template("signup.html", form=form)

        user = User(username=form.username.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("movies.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        password_ok = user is not None and user.check_password(form.password.data)
        blocked = user is not None and user.is_blocked
        success = password_ok and not blocked

        db.session.add(
            LoginAttempt(
                username=form.username.data,
                user_id=user.id if user else None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent", "")[:255],
                successful=success,
            )
        )

        if blocked:
            db.session.commit()
            flash("This account has been blocked by an administrator.", "danger")
            return render_template("login.html", form=form)

        if not success:
            db.session.commit()
            flash("Invalid username or password.", "danger")
            return render_template("login.html", form=form)

        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.remote_addr
        user.last_user_agent = request.headers.get("User-Agent", "")[:255]
        db.session.commit()

        login_user(user)
        next_page = request.args.get("next")
        flash(f"Welcome back, {user.username}!", "success")
        if _is_safe_next(next_page):
            return redirect(next_page)
        return redirect(url_for("admin.dashboard") if user.is_admin else url_for("movies.index"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("movies.index"))
