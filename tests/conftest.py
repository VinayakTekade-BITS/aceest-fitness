import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def alice_payload():
    return {"name": "Alice", "age": 28, "height_cm": 165, "weight_kg": 60, "program": "FL"}


@pytest.fixture
def alice(client, alice_payload):
    response = client.post("/clients", json=alice_payload)
    assert response.status_code == 201
    return response.get_json()
