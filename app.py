"""ACEest Fitness & Gym - Flask API entry point."""
import os
import socket
import sqlite3

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from aceest import BLUEPRINTS, db

HOSTNAME = socket.gethostname()


def create_app(config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = os.environ.get("ACEEST_DB", "aceest_fitness.db")
    app.config["APP_VERSION"] = os.environ.get("APP_VERSION", "dev")
    app.config["GIT_COMMIT"] = os.environ.get("GIT_COMMIT", "unknown")
    if config:
        app.config.update(config)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    @app.get("/")
    def index():
        return jsonify(
            app="ACEest Fitness & Gym", status="running", version=app.config["APP_VERSION"]
        )

    @app.get("/health")
    def health():
        """Liveness: the process is up and answering requests."""
        return jsonify(status="ok")

    @app.get("/ready")
    def ready():
        """Readiness: the database can be opened, so this instance may receive traffic."""
        try:
            with db.connect() as conn:
                conn.execute("SELECT 1")
        except sqlite3.Error as err:
            return jsonify(status="unavailable", error=str(err)), 503
        return jsonify(status="ready")

    @app.get("/version")
    def version():
        return jsonify(
            version=app.config["APP_VERSION"], commit=app.config["GIT_COMMIT"], host=HOSTNAME
        )

    @app.after_request
    def add_version_headers(response):
        # shows which version and which pod answered, e.g. during a canary or blue-green switch
        response.headers["X-App-Version"] = app.config["APP_VERSION"]
        response.headers["X-Served-By"] = HOSTNAME
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify(error=err.description), err.code

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
