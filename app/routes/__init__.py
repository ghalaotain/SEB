from .api import api_bp
from .advertisements import advertisements_bp
from .auth import auth_bp
from .pages import pages_bp
from .statistics import statistics_bp


def register_blueprints(app):
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(advertisements_bp)
