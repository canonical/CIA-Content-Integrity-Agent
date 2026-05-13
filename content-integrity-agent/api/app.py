import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory
from flask_cors import CORS
from api.extensions import db, socketio
from config.settings import Settings


def create_app(settings: Settings = None) -> Flask:
    if settings is None:
        settings = Settings.from_env()

    app = Flask(__name__, static_folder=None)

    db_path = settings.db_path
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", db_path))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app, origins=[settings.cors_origin])

    db.init_app(app)
    socketio.init_app(app)

    # Blueprint registrations - uncomment when routes are implemented
    # from api.routes.sites import sites_bp
    # from api.routes.sitemaps import sitemaps_bp
    # from api.routes.scans import scans_bp
    #
    # app.register_blueprint(sites_bp, url_prefix="/api/sites")
    # app.register_blueprint(sitemaps_bp, url_prefix="/api/sites")
    # app.register_blueprint(scans_bp, url_prefix="/api/scans")

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    with app.app_context():
        # from api.models import Site, Scan
        db.create_all()

    if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "web", "dist")):
        _register_static_routes(app)

    return app


def _register_static_routes(app: Flask):
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "dist"))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if path and os.path.exists(os.path.join(dist_dir, path)):
            return send_from_directory(dist_dir, path)
        return send_from_directory(dist_dir, "index.html")


def main():
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
