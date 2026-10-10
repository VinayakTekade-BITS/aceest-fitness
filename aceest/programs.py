"""Training programs carried over from the ACEest desktop app (v1.0 / v1.1)."""
from flask import Blueprint, abort, jsonify

PROGRAMS = {
    "FL": {
        "name": "Fat Loss",
        "workout": [
            "Mon: 5x5 Back Squat + AMRAP",
            "Tue: EMOM 20min Assault Bike",
            "Wed: Bench Press + 21-15-9",
            "Thu: 10RFT Deadlifts/Box Jumps",
            "Fri: 30min Active Recovery",
        ],
        "diet": [
            "B: 3 Egg Whites + Oats Idli",
            "L: Grilled Chicken + Brown Rice",
            "D: Fish Curry + Millet Roti",
        ],
        "calorie_factor": 22,
    },
    "MG": {
        "name": "Muscle Gain",
        "workout": [
            "Mon: Squat 5x5",
            "Tue: Bench 5x5",
            "Wed: Deadlift 4x6",
            "Thu: Front Squat 4x8",
            "Fri: Incline Press 4x10",
            "Sat: Barbell Rows 4x10",
        ],
        "diet": [
            "B: 4 Eggs + PB Oats",
            "L: Chicken Biryani (250g Chicken)",
            "D: Mutton Curry + Jeera Rice",
        ],
        "calorie_factor": 35,
    },
    "BG": {
        "name": "Beginner",
        "workout": [
            "Circuit Training: Air Squats, Ring Rows, Push-ups",
            "Focus: Technique Mastery & Form (90% Threshold)",
        ],
        "diet": [
            "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati",
            "Protein: 120g/day",
        ],
        "calorie_factor": 26,
    },
}

bp = Blueprint("programs", __name__)


@bp.get("/programs")
def list_programs():
    return jsonify([{"code": code, "name": p["name"]} for code, p in PROGRAMS.items()])


@bp.get("/programs/<code>")
def get_program(code):
    code = code.upper()
    program = PROGRAMS.get(code)
    if program is None:
        abort(404, description=f"Unknown program '{code}'")
    return jsonify(code=code, **program)
