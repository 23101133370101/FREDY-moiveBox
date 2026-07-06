import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-not-for-production")

    _database_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "moviehub.db"))
    if _database_url.startswith("postgres://"):
        # SQLAlchemy 1.4+ requires the "postgresql://" scheme; hosts like Render
        # still hand out "postgres://" URLs.
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, os.environ.get("UPLOAD_FOLDER", "uploads"))
    POSTER_FOLDER = os.path.join(basedir, os.environ.get("POSTER_FOLDER", "static/posters"))

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 2048)) * 1024 * 1024

    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mkv", "avi", "mov", "webm"}
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@moviehub.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    MOVIES_PER_PAGE = 12
