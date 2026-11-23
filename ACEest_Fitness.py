"""ACEest Fitness & Gym.

The original desktop application was a single Tkinter script (all versions are kept in
legacy/). This module keeps that name as the entry point of the Flask version:

    python ACEest_Fitness.py        # development server on http://127.0.0.1:5000
    gunicorn ACEest_Fitness:app     # production server (the Docker image uses app:app)
"""
import os

from app import app

__all__ = ["app"]

if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)))
