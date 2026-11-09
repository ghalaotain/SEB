from flask import (
    Blueprint,
    render_template,
)
from flask_login import login_required


pages_bp = Blueprint(
    "pages",
    __name__,
)


@pages_bp.get("/")
def home():
    return render_template(
        "home.html"
    )


@pages_bp.get("/display/ads")
def display_ads():
    return render_template(
        "display/ads.html"
    )


@pages_bp.get("/display/map")
def display_map():
    return render_template(
        "display/map.html"
    )


@pages_bp.get("/admin")
@login_required
def admin_dashboard():
    return render_template(
        "admin/dashboard.html"
    )