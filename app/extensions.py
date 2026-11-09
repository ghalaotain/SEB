from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)


login_manager.login_view = "auth.login"

login_manager.login_message = (
    "Please sign in to access the dashboard."
)

login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id: str):
    from .models import AdminUser

    try:
        admin_id = int(user_id)
    except (TypeError, ValueError):
        return None

    return db.session.get(
        AdminUser,
        admin_id,
    )