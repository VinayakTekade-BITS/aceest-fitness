"""Client profiles with calorie and BMI calculations (v1.1 - v2.2)."""
import sqlite3

from flask import Blueprint, abort, jsonify, request

from aceest import db
from aceest.programs import PROGRAMS

bp = Blueprint("clients", __name__)


def calculate_calories(weight_kg, program_code):
    """Daily calorie target: body weight x the program's calorie factor."""
    return int(weight_kg * PROGRAMS[program_code]["calorie_factor"])


def calculate_bmi(weight_kg, height_cm):
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("weight and height must be positive")
    bmi = round(weight_kg / (height_cm / 100) ** 2, 1)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return bmi, category


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object")
    return data


def positive_number(data, field):
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        abort(400, description=f"'{field}' must be a positive number")
    return value


def get_client_or_404(conn, name):
    row = conn.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    if row is None:
        abort(404, description=f"Client '{name}' not found")
    return row


@bp.post("/clients")
def create_client():
    data = json_body()
    name = str(data.get("name") or "").strip()
    if not name:
        abort(400, description="'name' is required")
    program = str(data.get("program") or "").upper()
    if program not in PROGRAMS:
        abort(400, description=f"'program' must be one of {', '.join(PROGRAMS)}")
    weight_kg = positive_number(data, "weight_kg")
    client = {
        "name": name,
        "age": positive_number(data, "age"),
        "height_cm": positive_number(data, "height_cm"),
        "weight_kg": weight_kg,
        "program": program,
        "calories": calculate_calories(weight_kg, program),
    }
    try:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO clients (name, age, height_cm, weight_kg, program, calories) "
                "VALUES (:name, :age, :height_cm, :weight_kg, :program, :calories)",
                client,
            )
    except sqlite3.IntegrityError:
        abort(409, description=f"Client '{name}' already exists")
    return jsonify(client), 201


@bp.get("/clients")
def list_clients():
    with db.connect() as conn:
        rows = conn.execute("SELECT name, program FROM clients ORDER BY name").fetchall()
    return jsonify([dict(row) for row in rows])


@bp.get("/clients/<name>")
def get_client(name):
    with db.connect() as conn:
        row = get_client_or_404(conn, name)
    return jsonify(dict(row))


@bp.get("/clients/<name>/bmi")
def client_bmi(name):
    with db.connect() as conn:
        row = get_client_or_404(conn, name)
    bmi, category = calculate_bmi(row["weight_kg"], row["height_cm"])
    return jsonify(name=name, bmi=bmi, category=category)
