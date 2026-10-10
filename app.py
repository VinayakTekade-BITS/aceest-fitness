"""ACEest Fitness & Gym - Flask API entry point."""
import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from aceest import BLUEPRINTS


def create_app(config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = os.environ.get("ACEEST_DB", "aceest_fitness.db")
    if config:
        app.config.update(config)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    @app.get("/")
    def index():
        return jsonify(app="ACEest Fitness & Gym", status="running")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify(error=err.description), err.code

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
