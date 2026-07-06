from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models.download import Download

users_bp = Blueprint("users", __name__)


@users_bp.route("/dashboard")
@login_required
def dashboard():
    downloads = (
        Download.query.filter_by(user_id=current_user.id)
        .order_by(Download.downloaded_at.desc())
        .all()
    )
    return render_template("dashboard.html", downloads=downloads)
