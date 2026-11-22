import time
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import OperationalError

from .config import Config
from .models import db

jwt = JWTManager()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    # --- JWT error handlers -> consistent JSON ---
    @jwt.unauthorized_loader
    def _missing_token(reason):
        return jsonify({"error": "Authentication required"}), 401

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return jsonify({"error": "Invalid token"}), 401

    @jwt.expired_token_loader
    def _expired_token(header, payload):
        return jsonify({"error": "Token expired"}), 401

    # --- Blueprints ---
    from .routes.auth import auth_bp
    from .routes.clubs import clubs_bp
    from .routes.events import events_bp
    from .routes.memberships import memberships_bp
    from .routes.broadcasts import broadcasts_bp
    from .routes.projects import projects_bp
    from .routes.notifications import notifications_bp
    from .routes.my import my_bp
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(memberships_bp)
    app.register_blueprint(broadcasts_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(my_bp)

    @app.errorhandler(404)
    def _nf(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def _ise(e):
        return jsonify({"error": "Internal server error"}), 500

    # Create tables on startup (retry so MySQL container has time to boot).
    with app.app_context():
        for attempt in range(10):
            try:
                db.create_all()
                break
            except OperationalError:
                if attempt == 9:
                    raise
                time.sleep(3)

    return app
