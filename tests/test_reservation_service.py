from datetime import date, timedelta

import pytest

from app import data_access
from app.modules import resource_reservation


@pytest.fixture(autouse=True)
def temporary_data(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)


@pytest.fixture
def visitor():
    return data_access.create("visitor", {
        "name": "Maya Brown", "phone_number": "876-555-0101",
        "type": "undergraduate", "student_id": "STU-01", "faculty": "Science",
        "purpose": "Research",
    })


@pytest.fixture
def room():
    return data_access.create("room", {
        "name": "Seminar Room", "capacity": 20,
        "status": "available", "condition": "good",
    })


@pytest.fixture
def book():
    return data_access.create("book", {
        "name": "Research Book", "author": "SALISES", "price": 1000,
        "genre": "Research", "status": "available", "condition": "good",
    })


def future_weekday():
    value = date.today() + timedelta(days=7)
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value.isoformat()


def test_create_room_reservation_validates_and_saves(visitor, room):
    saved, status = resource_reservation.create_reservation("room", {
        "visitor_id": visitor["id"], "resource_id": room["id"],
        "reserve_date": future_weekday(), "start_time": "10:00", "end_time": "11:00",
        "occupants": 5,
    })

    assert status == 201
    assert saved["reservation"]["status"] == "pending"
    assert saved["reservation"]["visitor_id"] == visitor["id"]
    assert saved["resource"]["name"] == room["name"]


@pytest.mark.parametrize("reservation_type", ["room", "archival", "book"])
def test_create_rejects_unknown_or_unavailable_resources(visitor, reservation_type):
    result, status = resource_reservation.create_reservation(reservation_type, {
        "visitor_id": visitor["id"], "resource_id": 29200099,
        "expected_return": (date.today() + timedelta(days=5)).isoformat(),
        "reserve_date": future_weekday(), "start_time": "10:00", "end_time": "11:00",
        "occupants": 1,
    })

    assert status == 404
    assert "Resource not found" in result["error"]


def test_create_rejects_invalid_payloads_and_unknown_visitor(room):
    invalid_type, invalid_type_status = resource_reservation.create_reservation("equipment", {})
    invalid_id, invalid_id_status = resource_reservation.create_reservation("room", {
        "visitor_id": "bad", "resource_id": room["id"],
    })
    unknown_visitor, unknown_visitor_status = resource_reservation.create_reservation("room", {
        "visitor_id": 19100099, "resource_id": room["id"],
    })

    assert invalid_type_status == 400
    assert invalid_id_status == 400
    assert unknown_visitor_status == 404


def test_approve_and_decline_update_pending_requests(visitor, room):
    payload = {"visitor_id": visitor["id"], "resource_id": room["id"],
               "reserve_date": future_weekday(), "start_time": "10:00",
               "end_time": "11:00", "occupants": 2}
    first, _ = resource_reservation.create_reservation("room", payload)
    second, _ = resource_reservation.create_reservation("room", payload)

    approved, approve_status = resource_reservation.approve_reservation(first["reservation"]["id"])
    declined, decline_status = resource_reservation.decline_reservation(second["reservation"]["id"])

    assert approve_status == 200 and approved["status"] == "approved"
    assert decline_status == 200 and declined["status"] == "declined"


def test_approval_rejects_overlapping_room_bookings(visitor, room):
    payload = {"visitor_id": visitor["id"], "resource_id": room["id"],
               "reserve_date": future_weekday(), "start_time": "10:00",
               "end_time": "11:00", "occupants": 2}
    first, _ = resource_reservation.create_reservation("room", payload)
    second, _ = resource_reservation.create_reservation("room", {
        **payload, "start_time": "10:30", "end_time": "11:30",
    })
    resource_reservation.approve_reservation(first["reservation"]["id"])

    result, status = resource_reservation.approve_reservation(second["reservation"]["id"])

    assert status == 409
    assert "overlaps" in result["error"]


def test_book_approval_and_return_release_book(visitor, book):
    reservation, status = resource_reservation.create_reservation("book", {
        "visitor_id": visitor["id"], "resource_id": book["id"],
        "expected_return": (date.today() + timedelta(days=10)).isoformat(),
    })
    reservation_id = reservation["reservation"]["id"]

    approved, approved_status = resource_reservation.approve_reservation(reservation_id)
    assert data_access.get_record("book", book["id"])["status"] == "reserved"
    returned, returned_status = resource_reservation.record_book_return(
        reservation_id, date.today().isoformat(),
    )

    assert status == 201 and approved_status == 200 and approved["status"] == "approved"
    assert returned_status == 200 and returned["actual_return"] == date.today()
    assert data_access.get_record("book", book["id"])["status"] == "available"


def test_transition_services_report_missing_and_invalid_requests():
    assert resource_reservation.approve_reservation(1)[1] == 404
    assert resource_reservation.decline_reservation(1)[1] == 404
    assert resource_reservation.cancel_reservation(1)[1] == 404
    assert resource_reservation.record_book_return(1, "2026-11-01")[1] == 404
