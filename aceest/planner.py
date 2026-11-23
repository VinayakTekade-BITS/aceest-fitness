"""Weekly workout plan generator (desktop v3.1.2 "AI program").

The desktop app picked exercises at random. The API rotates through the exercise pool
instead, so the same request always returns the same plan and the result can be tested.
"""
from flask import Blueprint, abort, jsonify, request

from aceest import db
from aceest.clients import get_client_or_404

bp = Blueprint("planner", __name__)

EXERCISE_POOLS = {
    "Conditioning": ["Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings"],
    "Hypertrophy": [
        "Leg Press",
        "Incline Dumbbell Press",
        "Lat Pulldown",
        "Lateral Raise",
        "Bicep Curl",
        "Tricep Extension",
    ],
    "Full Body": ["Push-Up", "Pull-Up", "Lunge", "Plank", "Dumbbell Row", "Dumbbell Press"],
}

FOCUS_BY_PROGRAM = {"FL": "Conditioning", "MG": "Hypertrophy", "BG": "Full Body"}

LEVELS = {
    "beginner": {"days": 3, "sets": "2-3", "reps": "8-12"},
    "intermediate": {"days": 4, "sets": "3-4", "reps": "8-15"},
    "advanced": {"days": 5, "sets": "4-5", "reps": "6-15"},
}

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def build_plan(program_code, experience):
    focus = FOCUS_BY_PROGRAM[program_code]
    level = LEVELS[experience]
    pool = EXERCISE_POOLS[focus]
    per_day = 3 if level["days"] < 4 else 4
    schedule = []
    for day_number, day in enumerate(WEEKDAYS[: level["days"]]):
        first = day_number * per_day
        names = [pool[(first + i) % len(pool)] for i in range(per_day)]
        exercises = [{"name": n, "sets": level["sets"], "reps": level["reps"]} for n in names]
        schedule.append({"day": day, "exercises": exercises})
    return {
        "focus": focus,
        "experience": experience,
        "days_per_week": level["days"],
        "schedule": schedule,
    }


@bp.get("/clients/<name>/plan")
def client_plan(name):
    experience = request.args.get("experience", "beginner").strip().lower()
    if experience not in LEVELS:
        abort(400, description=f"'experience' must be one of {', '.join(LEVELS)}")
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
    plan = build_plan(client["program"], experience)
    return jsonify(name=name, program=client["program"], **plan)
