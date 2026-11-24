from datetime import date, timedelta

import pytest

from app import data_access
from app.modules.authentication import create_user
from run import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-123")
    with app.test_client() as test_client:
        yield test_client


def headers(client, role):
    email = f"{role}@reservation.test"
    user, status = create_user({"name": role.title(), "email": email,
                                "password": "TestPass123", "role": role})
    assert status == 201
    response = client.post("/auth/login", json={"email": email, "password": "TestPass123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['access_token']}"}


@pytest.fixture
def setup_records():
    visitor = data_access.create("visitor", {
        "name": "Maya Brown", "phone_number": "876-555-0101",
        "type": "undergraduate", "student_id": "STU-01", "faculty": "Science",
        "purpose": "Research",
    })
    room = data_access.create("room", {
        "name": "Seminar Room", "capacity": 20, "status": "available", "condition": "good",
    })
    book = data_access.create("book", {
        "name": "Research Book", "author": "SALISES", "price": 1000,
        "genre": "Research", "status": "available", "condition": "good",
    })
    return visitor, room, book


def room_request(client, staff, visitor, room, **changes):
    next_day = date.today() + timedelta(days=7)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    data = {"visitor_id": visitor["id"], "resource_id": room["id"],
            "reserve_date": next_day.isoformat(), "start_time": "10:00",
            "end_time": "11:00", "occupants": 4}
    data.update(changes)
    response = client.post("/reservations/room", json=data, headers=staff)
    return response


def test_staff_submits_request_and_admin_approves(client, setup_records):
    visitor, room, _ = setup_records
    staff, admin = headers(client, "staff"), headers(client, "admin")

    submitted = room_request(client, staff, visitor, room)
    reservation = submitted.json["reservation"]
    approved = client.post(f"/reservations/{reservation['id']}/approve", headers=admin)

    assert submitted.status_code == 201
    assert reservation["status"] == "pending"
    assert approved.status_code == 200
    assert approved.json["status"] == "approved"


def test_book_request_approval_reserves_book(client, setup_records):
    visitor, _, book = setup_records
    staff, admin = headers(client, "staff"), headers(client, "admin")
    created = client.post("/reservations/book", json={
        "visitor_id": visitor["id"], "resource_id": book["id"],
        "expected_return": (date.today() + timedelta(days=10)).isoformat(),
    }, headers=staff)

    response = client.post(f"/reservations/{created.json['reservation']['id']}/approve", headers=admin)

    assert response.status_code == 200
    assert data_access.get_record("book", book["id"])["status"] == "reserved"


def test_admin_declines_pending_request(client, setup_records):
    visitor, room, _ = setup_records
    staff, admin = headers(client, "staff"), headers(client, "admin")
    created = room_request(client, staff, visitor, room)

    response = client.post(f"/reservations/{created.json['reservation']['id']}/decline", headers=admin)

    assert response.status_code == 200
    assert response.json["status"] == "declined"


def test_staff_can_cancel_future_room_request(client, setup_records):
    visitor, room, _ = setup_records
    staff = headers(client, "staff")
    created = room_request(client, staff, visitor, room)

    response = client.post(f"/reservations/{created.json['reservation']['id']}/cancel", headers=staff)

    assert response.status_code == 200
    assert response.json["status"] == "cancelled"


def test_staff_records_book_return(client, setup_records):
    visitor, _, book = setup_records
    staff, admin = headers(client, "staff"), headers(client, "admin")
    created = client.post("/reservations/book", json={
        "visitor_id": visitor["id"], "resource_id": book["id"],
        "expected_return": (date.today() + timedelta(days=10)).isoformat(),
    }, headers=staff)
    reservation_id = created.json["reservation"]["id"]
    client.post(f"/reservations/{reservation_id}/approve", headers=admin)

    returned = client.post(f"/reservations/{reservation_id}/return",
                           json={"actual_return": date.today().isoformat()}, headers=staff)

    assert returned.status_code == 200
    assert returned.json["actual_return"] == date.today().isoformat()
    assert data_access.get_record("book", book["id"])["status"] == "available"


def test_reservation_endpoints_enforce_roles_and_login(client, setup_records):
    visitor, room, _ = setup_records
    staff, admin = headers(client, "staff"), headers(client, "admin")
    created = room_request(client, staff, visitor, room)
    reservation_id = created.json["reservation"]["id"]

    assert client.post("/reservations/room", json={}).status_code == 401
    assert client.post("/reservations/room", json={}, headers=admin).status_code == 403
    assert client.post(f"/reservations/{reservation_id}/approve", headers=staff).status_code == 403
    assert client.post(f"/reservations/{reservation_id}/decline", headers=staff).status_code == 403
    assert client.post(f"/reservations/{reservation_id}/cancel", headers=admin).status_code == 403


def test_reservation_validation_and_unknown_ids(client, setup_records):
    visitor, _, _ = setup_records
    staff, admin = headers(client, "staff"), headers(client, "admin")

    invalid = client.post("/reservations/room", json={
        "visitor_id": visitor["id"], "resource_id": 39300099,
        "reserve_date": "2026-11-27", "start_time": "10:00", "end_time": "11:00",
        "occupants": 2,
    }, headers=staff)
    missing = client.post("/reservations/book", headers=staff)
    approve_missing = client.post("/reservations/69600099/approve", headers=admin)

    assert invalid.status_code == 404
    assert missing.status_code == 400
    assert approve_missing.status_code == 404
