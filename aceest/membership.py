"""Membership renewal and status checks (v3.2)."""
from datetime import date, timedelta

from flask import Blueprint, abort, jsonify

from aceest import db
from aceest.clients import get_client_or_404, json_body

bp = Blueprint("membership", __name__)

DAYS_PER_MONTH = 30


def membership_status(end_date, today):
    if end_date is None:
        return "Inactive"
    return "Active" if date.fromisoformat(end_date) >= today else "Expired"


def extend_membership(end_date, months, today):
    """Renewals stack on an active membership; expired ones restart today."""
    start = today
    if end_date is not None:
        start = max(today, date.fromisoformat(end_date))
    return start + timedelta(days=DAYS_PER_MONTH * months)


@bp.get("/clients/<name>/membership")
def get_membership(name):
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
    end = client["membership_end"]
    return jsonify(name=name, status=membership_status(end, date.today()), membership_end=end)


@bp.post("/clients/<name>/membership")
def renew_membership(name):
    months = json_body().get("months")
    if isinstance(months, bool) or not isinstance(months, int) or not 1 <= months <= 24:
        abort(400, description="'months' must be an integer between 1 and 24")
    today = date.today()
    with db.connect() as conn:
        client = get_client_or_404(conn, name)
        new_end = extend_membership(client["membership_end"], months, today).isoformat()
        conn.execute(
            "UPDATE clients SET membership_end = ? WHERE id = ?", (new_end, client["id"])
        )
    return jsonify(name=name, status=membership_status(new_end, today), membership_end=new_end)
