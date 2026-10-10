from datetime import date, timedelta

import pytest

from aceest.membership import extend_membership, membership_status

TODAY = date(2026, 3, 15)


def test_membership_status():
    assert membership_status(None, TODAY) == "Inactive"
    assert membership_status("2026-03-15", TODAY) == "Active"
    assert membership_status("2026-03-14", TODAY) == "Expired"


def test_extend_starts_today_when_inactive_or_expired():
    assert extend_membership(None, 1, TODAY) == date(2026, 4, 14)
    assert extend_membership("2026-01-01", 1, TODAY) == date(2026, 4, 14)


def test_extend_stacks_on_active_membership():
    assert extend_membership("2026-04-01", 2, TODAY) == date(2026, 5, 31)


def test_new_client_is_inactive(client, alice):
    body = client.get("/clients/Alice/membership").get_json()
    assert body == {"name": "Alice", "status": "Inactive", "membership_end": None}


def test_renew_activates_membership(client, alice):
    response = client.post("/clients/Alice/membership", json={"months": 3})
    assert response.status_code == 200
    expected_end = (date.today() + timedelta(days=90)).isoformat()
    assert response.get_json() == {
        "name": "Alice",
        "status": "Active",
        "membership_end": expected_end,
    }
    assert client.get("/clients/Alice/membership").get_json()["status"] == "Active"


def test_renewals_stack(client, alice):
    client.post("/clients/Alice/membership", json={"months": 1})
    body = client.post("/clients/Alice/membership", json={"months": 1}).get_json()
    assert body["membership_end"] == (date.today() + timedelta(days=60)).isoformat()


@pytest.mark.parametrize("months", [0, 25, "six", None, True])
def test_invalid_months_rejected(client, alice, months):
    assert client.post("/clients/Alice/membership", json={"months": months}).status_code == 400


def test_membership_unknown_client(client):
    assert client.get("/clients/Ghost/membership").status_code == 404
