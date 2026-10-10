from datetime import date

import pytest


def test_log_and_list_progress(client, alice):
    response = client.post("/clients/Alice/progress", json={"week": "2026-W10", "adherence": 85})
    assert response.status_code == 201
    assert client.get("/clients/Alice/progress").get_json() == [
        {"week": "2026-W10", "adherence": 85}
    ]


@pytest.mark.parametrize("adherence", [-1, 101, "high", True, None])
def test_invalid_adherence_rejected(client, alice, adherence):
    response = client.post(
        "/clients/Alice/progress", json={"week": "2026-W10", "adherence": adherence}
    )
    assert response.status_code == 400


def test_progress_requires_week(client, alice):
    assert client.post("/clients/Alice/progress", json={"adherence": 50}).status_code == 400


def test_progress_for_unknown_client(client):
    response = client.post("/clients/Ghost/progress", json={"week": "2026-W10", "adherence": 50})
    assert response.status_code == 404


def test_log_and_list_workouts(client, alice):
    workout = {
        "date": "2026-03-01",
        "workout_type": "Strength",
        "duration_min": 45,
        "notes": "5x5 back squat",
    }
    response = client.post("/clients/Alice/workouts", json=workout)
    assert response.status_code == 201
    assert client.get("/clients/Alice/workouts").get_json() == [workout]


def test_workout_date_defaults_to_today(client, alice):
    response = client.post(
        "/clients/Alice/workouts", json={"workout_type": "Cardio", "duration_min": 30}
    )
    assert response.get_json()["date"] == date.today().isoformat()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"workout_type": "Cardio"},
        {"workout_type": "Cardio", "duration_min": 0},
        {"workout_type": "Cardio", "duration_min": 30, "date": "01-03-2026"},
    ],
)
def test_invalid_workout_rejected(client, alice, payload):
    assert client.post("/clients/Alice/workouts", json=payload).status_code == 400


def test_workouts_for_unknown_client(client):
    assert client.get("/clients/Ghost/workouts").status_code == 404
