from datetime import datetime

from database import db


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(100), nullable=True, index=True)
    year = db.Column(db.Integer, nullable=True)

    poster_filename = db.Column(db.String(255), nullable=True)
    video_filename = db.Column(db.String(255), nullable=False)
    file_size_mb = db.Column(db.Float, nullable=True)

    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    download_count = db.Column(db.Integer, default=0, nullable=False)

    downloads = db.relationship("Download", backref="movie", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Movie {self.title} ({self.year})>"
