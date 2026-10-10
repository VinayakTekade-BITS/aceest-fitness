"""Weekly adherence and workout logging (v2.x)."""
from datetime import date

from flask import Blueprint, abort, jsonify

from aceest import db
from aceest.clients import get_client_or_404, json_body, positive_number

bp = Blueprint("tracking", __name__)


@bp.post("/clients/<name>/progress")
def log_progress(name):
    data = json_body()
    week = str(data.get("week") or "").strip()
    if not week:
        abort(400, description="'week' is required")
    adherence = data.get("adherence")
    if isinstance(adherence, bool) or not isinstance(adherence, int) or not 0 <= adherence <= 100:
        abort(400, description="'adherence' must be an integer between 0 and 100")
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        conn.execute(
            "INSERT INTO progress (client_id, week, adherence) VALUES (?, ?, ?)",
            (client["id"], week, adherence),
        )
    return jsonify(name=name, week=week, adherence=adherence), 201


@bp.get("/clients/<name>/progress")
def list_progress(name):
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        rows = conn.execute(
            "SELECT week, adherence FROM progress WHERE client_id = ? ORDER BY id",
            (client["id"],),
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@bp.post("/clients/<name>/workouts")
def log_workout(name):
    data = json_body()
    workout_type = str(data.get("workout_type") or "").strip()
    if not workout_type:
        abort(400, description="'workout_type' is required")
    duration_min = positive_number(data, "duration_min")
    workout_date = data.get("date") or date.today().isoformat()
    try:
        date.fromisoformat(workout_date)
    except (TypeError, ValueError):
        abort(400, description="'date' must be in YYYY-MM-DD format")
    workout = {
        "date": workout_date,
        "workout_type": workout_type,
        "duration_min": duration_min,
        "notes": str(data.get("notes") or ""),
    }
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        conn.execute(
            "INSERT INTO workouts (client_id, date, workout_type, duration_min, notes) "
            "VALUES (:client_id, :date, :workout_type, :duration_min, :notes)",
            {"client_id": client["id"], **workout},
        )
    return jsonify(name=name, **workout), 201


@bp.get("/clients/<name>/workouts")
def list_workouts(name):
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        rows = conn.execute(
            "SELECT date, workout_type, duration_min, notes FROM workouts "
            "WHERE client_id = ? ORDER BY date, id",
            (client["id"],),
        ).fetchall()
    return jsonify([dict(row) for row in rows])
