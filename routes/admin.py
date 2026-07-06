import os
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from werkzeug.utils import secure_filename

from database import db
from models.movie import Movie
from models.user import User
from models.login_attempt import LoginAttempt

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


class UploadMovieForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    genre = StringField("Genre", validators=[Optional(), Length(max=100)])
    year = IntegerField("Year", validators=[Optional(), NumberRange(min=1888, max=2100)])
    poster = FileField("Poster Image", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"])])
    video = FileField(
        "Movie File", validators=[FileRequired(), FileAllowed(["mp4", "mkv", "avi", "mov", "webm"])]
    )
    submit = SubmitField("Upload Movie")


class SettingsForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_username = StringField("New Username", validators=[Optional(), Length(min=3, max=80)])
    new_password = PasswordField("New Password", validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField("Confirm New Password", validators=[Optional()])
    submit = SubmitField("Save Changes")


def _allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    stats = {
        "total_users": User.query.count(),
        "blocked_users": User.query.filter_by(is_blocked=True).count(),
        "failed_logins_today": LoginAttempt.query.filter(
            LoginAttempt.successful.is_(False),
            LoginAttempt.created_at >= datetime.utcnow().date(),
        ).count(),
    }
    return render_template("admin_dashboard.html", movies=movies, stats=stats)


@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload_movie():
    form = UploadMovieForm()
    if form.validate_on_submit():
        video_file = form.video.data
        video_filename = secure_filename(video_file.filename)

        if not _allowed_file(video_filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"]):
            flash("Unsupported video file type.", "danger")
            return render_template("upload.html", form=form)

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)

        base, ext = os.path.splitext(video_filename)
        stored_video_name = video_filename
        counter = 1
        while os.path.exists(os.path.join(upload_dir, stored_video_name)):
            stored_video_name = f"{base}_{counter}{ext}"
            counter += 1

        video_path = os.path.join(upload_dir, stored_video_name)
        video_file.save(video_path)
        file_size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 2)

        poster_filename = None
        poster_file = form.poster.data
        if poster_file and poster_file.filename:
            raw_poster_name = secure_filename(poster_file.filename)
            if not _allowed_file(raw_poster_name, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                flash("Unsupported poster image type.", "danger")
                return render_template("upload.html", form=form)

            poster_dir = current_app.config["POSTER_FOLDER"]
            os.makedirs(poster_dir, exist_ok=True)

            base_p, ext_p = os.path.splitext(raw_poster_name)
            poster_filename = raw_poster_name
            counter = 1
            while os.path.exists(os.path.join(poster_dir, poster_filename)):
                poster_filename = f"{base_p}_{counter}{ext_p}"
                counter += 1

            poster_file.save(os.path.join(poster_dir, poster_filename))

        movie = Movie(
            title=form.title.data,
            description=form.description.data,
            genre=form.genre.data,
            year=form.year.data,
            poster_filename=poster_filename,
            video_filename=stored_video_name,
            file_size_mb=file_size_mb,
            uploaded_by=current_user.id,
        )
        db.session.add(movie)
        db.session.commit()

        flash(f'"{movie.title}" uploaded successfully.', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("upload.html", form=form)


@admin_bp.route("/movies/<int:movie_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    video_path = os.path.join(current_app.config["UPLOAD_FOLDER"], movie.video_filename)
    if os.path.isfile(video_path):
        os.remove(video_path)

    if movie.poster_filename:
        poster_path = os.path.join(current_app.config["POSTER_FOLDER"], movie.poster_filename)
        if os.path.isfile(poster_path):
            os.remove(poster_path)

    db.session.delete(movie)
    db.session.commit()

    flash(f'"{movie.title}" was deleted.', "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot change your own admin status.", "warning")
        return redirect(url_for("admin.users_info"))

    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Updated admin status for {user.username}.", "success")
    return redirect(url_for("admin.users_info"))


@admin_bp.route("/users-info")
@login_required
@admin_required
def users_info():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users_info.html", users=users)


@admin_bp.route("/firewall")
@login_required
@admin_required
def firewall():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_firewall.html", users=users)


@admin_bp.route("/users/<int:user_id>/toggle-block", methods=["POST"])
@login_required
@admin_required
def toggle_block(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot block yourself.", "warning")
        return redirect(url_for("admin.firewall"))
    if user.is_admin:
        flash("Revoke admin status before blocking this user.", "warning")
        return redirect(url_for("admin.firewall"))

    user.is_blocked = not user.is_blocked
    db.session.commit()
    flash(f"{'Blocked' if user.is_blocked else 'Unblocked'} {user.username}.", "success")
    return redirect(url_for("admin.firewall"))


@admin_bp.route("/login-attempts")
@login_required
@admin_required
def login_attempts():
    attempts = LoginAttempt.query.order_by(LoginAttempt.created_at.desc()).limit(200).all()
    return render_template("admin_login_attempts.html", attempts=attempts)


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("admin_settings.html", form=form)

        new_username = form.new_username.data.strip() if form.new_username.data else None
        if new_username and new_username != current_user.username:
            if User.query.filter(User.username == new_username, User.id != current_user.id).first():
                flash("That username is already taken.", "danger")
                return render_template("admin_settings.html", form=form)
            current_user.username = new_username

        if form.new_password.data:
            if form.new_password.data != form.confirm_new_password.data:
                flash("New password and confirmation do not match.", "danger")
                return render_template("admin_settings.html", form=form)
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin_settings.html", form=form)
