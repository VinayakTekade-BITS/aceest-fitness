"""Endpoints and headers used by Kubernetes probes and the deployment strategies."""
import ACEest_Fitness
from app import app as module_app
from app import create_app


def make_app(tmp_path, **config):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db"), **config})


def test_version_endpoint(tmp_path):
    app = make_app(tmp_path, APP_VERSION="9.9.9", GIT_COMMIT="abc1234")
    body = app.test_client().get("/version").get_json()
    assert body["version"] == "9.9.9"
    assert body["commit"] == "abc1234"
    assert body["host"]


def test_index_reports_version(tmp_path):
    app = make_app(tmp_path, APP_VERSION="9.9.9")
    assert app.test_client().get("/").get_json()["version"] == "9.9.9"


def test_every_response_has_version_headers(tmp_path):
    client = make_app(tmp_path, APP_VERSION="9.9.9").test_client()
    for path in ["/health", "/programs", "/does-not-exist"]:
        response = client.get(path)
        assert response.headers["X-App-Version"] == "9.9.9"
        assert response.headers["X-Served-By"]


def test_ready_when_database_is_available(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_not_ready_when_database_cannot_be_opened(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "missing" / "test.db")})
    response = app.test_client().get("/ready")
    assert response.status_code == 503
    assert response.get_json()["status"] == "unavailable"


def test_entry_point_exposes_the_flask_app():
    assert ACEest_Fitness.app is module_app
