import pytest

from aceest.clients import calculate_bmi, calculate_calories


def test_calculate_calories_uses_program_factor():
    assert calculate_calories(60, "FL") == 1320
    assert calculate_calories(60, "MG") == 2100
    assert calculate_calories(60, "BG") == 1560


@pytest.mark.parametrize(
    "weight, height, category",
    [(50, 180, "Underweight"), (65, 175, "Normal"), (85, 175, "Overweight"), (110, 175, "Obese")],
)
def test_calculate_bmi_categories(weight, height, category):
    assert calculate_bmi(weight, height)[1] == category


def test_calculate_bmi_value():
    assert calculate_bmi(60, 165) == (22.0, "Normal")


def test_calculate_bmi_rejects_non_positive():
    with pytest.raises(ValueError):
        calculate_bmi(0, 170)


def test_create_client(client, alice_payload):
    response = client.post("/clients", json=alice_payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Alice"
    assert body["calories"] == 1320


def test_program_code_is_case_insensitive(client, alice_payload):
    response = client.post("/clients", json={**alice_payload, "program": "mg"})
    assert response.status_code == 201
    assert response.get_json()["program"] == "MG"


def test_get_client(client, alice):
    body = client.get("/clients/Alice").get_json()
    assert body["program"] == "FL"
    assert body["weight_kg"] == 60


def test_list_clients(client, alice):
    assert client.get("/clients").get_json() == [{"name": "Alice", "program": "FL"}]


def test_duplicate_client_conflict(client, alice, alice_payload):
    assert client.post("/clients", json=alice_payload).status_code == 409


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", ""),
        ("program", "XX"),
        ("age", -1),
        ("age", True),
        ("height_cm", None),
        ("weight_kg", "heavy"),
    ],
)
def test_invalid_client_rejected(client, alice_payload, field, value):
    response = client.post("/clients", json={**alice_payload, field: value})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_non_json_body_rejected(client):
    assert client.post("/clients", data="not json").status_code == 400


def test_unknown_client_returns_404(client):
    assert client.get("/clients/Ghost").status_code == 404


def test_client_bmi(client, alice):
    body = client.get("/clients/Alice/bmi").get_json()
    assert body == {"name": "Alice", "bmi": 22.0, "category": "Normal"}
