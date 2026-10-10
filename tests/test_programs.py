import pytest


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["status"] == "running"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_list_programs(client):
    codes = {p["code"] for p in client.get("/programs").get_json()}
    assert codes == {"FL", "MG", "BG"}


@pytest.mark.parametrize("code", ["FL", "mg", "Bg"])
def test_get_program_is_case_insensitive(client, code):
    response = client.get(f"/programs/{code}")
    assert response.status_code == 200
    body = response.get_json()
    assert body["code"] == code.upper()
    assert body["workout"] and body["diet"]


def test_unknown_program_returns_json_404(client):
    response = client.get("/programs/XYZ")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_unknown_route_returns_json_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.get_json()
