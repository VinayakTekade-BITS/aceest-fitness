from datetime import date

import pytest


def test_log_and_list_metrics(client, alice):
    entry = {"date": "2026-03-01", "weight_kg": 59.5, "waist_cm": 72, "bodyfat_pct": 24.5}
    response = client.post("/clients/Alice/metrics", json=entry)
    assert response.status_code == 201
    assert response.get_json() == {"name": "Alice", **entry}
    assert client.get("/clients/Alice/metrics").get_json() == [entry]


def test_metrics_date_defaults_to_today(client, alice):
    body = client.post("/clients/Alice/metrics", json={"weight_kg": 60}).get_json()
    assert body["date"] == date.today().isoformat()
    assert body["waist_cm"] is None
    assert body["bodyfat_pct"] is None


def test_metrics_are_listed_by_date(client, alice):
    client.post("/clients/Alice/metrics", json={"date": "2026-03-08", "weight_kg": 59})
    client.post("/clients/Alice/metrics", json={"date": "2026-03-01", "weight_kg": 60})
    dates = [m["date"] for m in client.get("/clients/Alice/metrics").get_json()]
    assert dates == ["2026-03-01", "2026-03-08"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"weight_kg": 0},
        {"weight_kg": "heavy"},
        {"weight_kg": 60, "waist_cm": -5},
        {"weight_kg": 60, "bodyfat_pct": 100},
        {"weight_kg": 60, "date": "01-03-2026"},
    ],
)
def test_invalid_metrics_rejected(client, alice, payload):
    response = client.post("/clients/Alice/metrics", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_metrics_for_unknown_client(client):
    assert client.post("/clients/Ghost/metrics", json={"weight_kg": 60}).status_code == 404
    assert client.get("/clients/Ghost/metrics").status_code == 404


def test_summary_of_new_client(client, alice):
    assert client.get("/clients/Alice/summary").get_json() == {
        "name": "Alice",
        "program": "FL",
        "calories": 1320,
        "membership": "Inactive",
        "progress": {"weeks_logged": 0, "average_adherence": None},
        "workouts": {"sessions": 0, "total_minutes": 0},
        "latest_metrics": None,
        "bmi": {"value": 22.0, "category": "Normal"},
    }


def test_summary_aggregates_activity(client, alice):
    client.post("/clients/Alice/progress", json={"week": "2026-W10", "adherence": 80})
    client.post("/clients/Alice/progress", json={"week": "2026-W11", "adherence": 95})
    client.post("/clients/Alice/workouts", json={"workout_type": "Strength", "duration_min": 45})
    client.post("/clients/Alice/workouts", json={"workout_type": "Cardio", "duration_min": 30})
    client.post("/clients/Alice/metrics", json={"date": "2026-03-01", "weight_kg": 70})
    client.post("/clients/Alice/membership", json={"months": 1})

    body = client.get("/clients/Alice/summary").get_json()
    assert body["progress"] == {"weeks_logged": 2, "average_adherence": 87.5}
    assert body["workouts"] == {"sessions": 2, "total_minutes": 75}
    assert body["latest_metrics"]["weight_kg"] == 70
    assert body["membership"] == "Active"
    # the latest measured weight is used: 70 kg at 165 cm
    assert body["bmi"] == {"value": 25.7, "category": "Overweight"}


def test_summary_for_unknown_client(client):
    assert client.get("/clients/Ghost/summary").status_code == 404
