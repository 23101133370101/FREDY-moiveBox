import os

from flask import (
    Blueprint,
    render_template,
    request,
    send_from_directory,
    current_app,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

from database import db
from models.movie import Movie
from models.download import Download

movies_bp = Blueprint("movies", __name__)


@movies_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "", type=str).strip()
    genre = request.args.get("genre", "", type=str).strip()

    query = Movie.query
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))
    if genre:
        query = query.filter(Movie.genre.ilike(genre))

    pagination = query.order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=current_app.config["MOVIES_PER_PAGE"], error_out=False
    )

    genres = [g[0] for g in db.session.query(Movie.genre).filter(Movie.genre.isnot(None)).distinct()]

    return render_template(
        "index.html",
        movies=pagination.items,
        pagination=pagination,
        search=search,
        selected_genre=genre,
        genres=genres,
    )


@movies_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template("movie_details.html", movie=movie)


@movies_bp.route("/movie/<int:movie_id>/download")
@login_required
def download_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_dir, movie.video_filename)
    if not os.path.isfile(file_path):
        flash("The requested file is no longer available.", "danger")
        return redirect(url_for("movies.movie_details", movie_id=movie.id))

    movie.download_count += 1
    db.session.add(
        Download(user_id=current_user.id, movie_id=movie.id, ip_address=request.remote_addr)
    )
    db.session.commit()

    return send_from_directory(upload_dir, movie.video_filename, as_attachment=True)
