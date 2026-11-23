import pytest

from aceest.planner import EXERCISE_POOLS, build_plan


@pytest.mark.parametrize(
    "experience, days, per_day", [("beginner", 3, 3), ("intermediate", 4, 4), ("advanced", 5, 4)]
)
def test_plan_size_depends_on_experience(experience, days, per_day):
    plan = build_plan("BG", experience)
    assert plan["days_per_week"] == days
    assert len(plan["schedule"]) == days
    assert all(len(day["exercises"]) == per_day for day in plan["schedule"])


@pytest.mark.parametrize(
    "program, focus", [("FL", "Conditioning"), ("MG", "Hypertrophy"), ("BG", "Full Body")]
)
def test_plan_focus_follows_program(program, focus):
    plan = build_plan(program, "intermediate")
    assert plan["focus"] == focus
    names = {e["name"] for day in plan["schedule"] for e in day["exercises"]}
    assert names <= set(EXERCISE_POOLS[focus])


def test_no_exercise_repeats_within_a_day():
    for day in build_plan("MG", "advanced")["schedule"]:
        names = [e["name"] for e in day["exercises"]]
        assert len(names) == len(set(names))


def test_plan_is_deterministic():
    first = build_plan("FL", "advanced")
    second = build_plan("FL", "advanced")
    assert first == second


def test_plan_endpoint(client, alice):
    response = client.get("/clients/Alice/plan?experience=Intermediate")
    assert response.status_code == 200
    body = response.get_json()
    assert body["program"] == "FL"
    assert body["focus"] == "Conditioning"
    assert body["experience"] == "intermediate"
    assert body["schedule"][0] == {
        "day": "Monday",
        "exercises": [
            {"name": "Running", "sets": "3-4", "reps": "8-15"},
            {"name": "Cycling", "sets": "3-4", "reps": "8-15"},
            {"name": "Rowing", "sets": "3-4", "reps": "8-15"},
            {"name": "Burpees", "sets": "3-4", "reps": "8-15"},
        ],
    }


def test_plan_defaults_to_beginner(client, alice):
    assert client.get("/clients/Alice/plan").get_json()["experience"] == "beginner"


def test_plan_rejects_unknown_experience(client, alice):
    assert client.get("/clients/Alice/plan?experience=expert").status_code == 400


def test_plan_for_unknown_client(client):
    assert client.get("/clients/Ghost/plan").status_code == 404
