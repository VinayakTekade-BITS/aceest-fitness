"""Body metrics log and client progress summary (desktop v2.2.4 / v3.0.1)."""
from datetime import date

from flask import Blueprint, abort, jsonify

from aceest import db
from aceest.clients import calculate_bmi, get_client_or_404, json_body, positive_number
from aceest.membership import membership_status

bp = Blueprint("metrics", __name__)


def measurement_date(data):
    """The 'date' field as YYYY-MM-DD; today if it is missing."""
    value = data.get("date") or date.today().isoformat()
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        abort(400, description="'date' must be in YYYY-MM-DD format")


def optional_measure(data, field, below=None):
    """An optional positive number, optionally with an upper bound."""
    if data.get(field) is None:
        return None
    value = positive_number(data, field)
    if below is not None and value >= below:
        abort(400, description=f"'{field}' must be below {below}")
    return value


@bp.post("/clients/<name>/metrics")
def log_metrics(name):
    data = json_body()
    entry = {
        "date": measurement_date(data),
        "weight_kg": positive_number(data, "weight_kg"),
        "waist_cm": optional_measure(data, "waist_cm"),
        "bodyfat_pct": optional_measure(data, "bodyfat_pct", below=100),
    }
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        conn.execute(
            "INSERT INTO metrics (client_id, date, weight_kg, waist_cm, bodyfat_pct) "
            "VALUES (:client_id, :date, :weight_kg, :waist_cm, :bodyfat_pct)",
            {"client_id": client["id"], **entry},
        )
    return jsonify(name=name, **entry), 201


@bp.get("/clients/<name>/metrics")
def list_metrics(name):
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        rows = conn.execute(
            "SELECT date, weight_kg, waist_cm, bodyfat_pct FROM metrics "
            "WHERE client_id = ? ORDER BY date, id",
            (client["id"],),
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/clients/<name>/summary")
def client_summary(name):
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        client_id = (client["id"],)
        progress = conn.execute(
            "SELECT COUNT(*) AS weeks, AVG(adherence) AS average FROM progress "
            "WHERE client_id = ?",
            client_id,
        ).fetchone()
        workouts = conn.execute(
            "SELECT COUNT(*) AS sessions, COALESCE(SUM(duration_min), 0) AS minutes "
            "FROM workouts WHERE client_id = ?",
            client_id,
        ).fetchone()
        latest = conn.execute(
            "SELECT date, weight_kg, waist_cm, bodyfat_pct FROM metrics "
            "WHERE client_id = ? ORDER BY date DESC, id DESC LIMIT 1",
            client_id,
        ).fetchone()

    # BMI uses the most recent measured weight, or the profile weight if none was logged
    weight = latest["weight_kg"] if latest else client["weight_kg"]
    bmi, category = calculate_bmi(weight, client["height_cm"])
    average = progress["average"]
    return jsonify(
        name=name,
        program=client["program"],
        calories=client["calories"],
        membership=membership_status(client["membership_end"], date.today()),
        progress={
            "weeks_logged": progress["weeks"],
            "average_adherence": None if average is None else round(average, 1),
        },
        workouts={"sessions": workouts["sessions"], "total_minutes": workouts["minutes"]},
        latest_metrics=dict(latest) if latest else None,
        bmi={"value": bmi, "category": category},
    )
