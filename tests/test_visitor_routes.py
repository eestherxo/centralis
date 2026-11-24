from datetime import datetime

import pytest

from app import data_access
from run import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-123")
    with app.test_client() as test_client:
        yield test_client


def student_data(**changes):
    data = {
        "name": "Taylor Smith", "phone_number": "876-555-0123",
        "student_id": "STU-123", "faculty": "Science",
        "purpose": "Research", "type": "undergraduate",
    }
    data.update(changes)
    return data


def test_registration_creates_visitor_and_open_visit(client):
    response = client.post("/visitors/register", json=student_data())

    assert response.status_code == 201
    assert response.json["visitor"]["student_id"] == "STU-123"
    assert response.json["visit"]["visitor_id"] == response.json["visitor"]["id"]
    assert response.json["visit"]["check_out"] is None
    assert datetime.fromisoformat(response.json["visit"]["check_in"])
    assert len(data_access.get_all_records("visitor")) == 1
    assert len(data_access.get_all_records("visit")) == 1


@pytest.mark.parametrize("visitor_type", ["undergraduate", "postgraduate"])
def test_student_registration_requires_student_fields(client, visitor_type):
    response = client.post("/visitors/register", json=student_data(
        type=visitor_type, student_id="", faculty="",
    ))

    assert response.status_code == 400
    assert {"student_id", "faculty"} <= response.json["fields"].keys()
    assert data_access.get_all_records("visitor") == []


def test_external_registration_does_not_require_student_fields(client):
    response = client.post("/visitors/register", json={
        "name": "Morgan Brown", "phone_number": "876-555-0456",
        "purpose": "Seminar", "type": "external",
    })

    assert response.status_code == 201
    assert response.json["visitor"]["student_id"] is None
    assert response.json["visitor"]["faculty"] is None


def test_external_registration_rejects_student_id(client):
    response = client.post("/visitors/register", json=student_data(
        type="external", student_id="STU-123",
    ))

    assert response.status_code == 400
    assert "student_id" in response.json["fields"]


def test_registration_rejects_invalid_fields_and_type(client):
    missing = client.post("/visitors/register", json=student_data(phone_number=" "))
    invalid_type = client.post("/visitors/register", json=student_data(type="visitor"))
    no_json = client.post("/visitors/register", data="invalid", content_type="text/plain")

    assert missing.status_code == 400
    assert "phone_number" in missing.json["fields"]
    assert invalid_type.status_code == 400
    assert "type" in invalid_type.json["fields"]
    assert no_json.status_code == 400
    assert data_access.get_all_records("visitor") == []


def test_duplicate_student_registration_is_rejected_case_insensitively(client):
    assert client.post("/visitors/register", json=student_data()).status_code == 201

    duplicate = client.post("/visitors/register", json=student_data(student_id=" stu-123 "))

    assert duplicate.status_code == 409
    assert len(data_access.get_all_records("visitor")) == 1
    assert len(data_access.get_all_records("visit")) == 1


def test_external_duplicate_matches_name_and_phone(client):
    data = {
        "name": "Morgan Brown", "phone_number": "876-555-0456",
        "purpose": "Seminar", "type": "external",
    }
    assert client.post("/visitors/register", json=data).status_code == 201
    duplicate = client.post("/visitors/register", json={
        **data, "name": " morgan brown ", "phone_number": "(876) 555-0456",
    })

    assert duplicate.status_code == 409


def test_check_in_and_check_out_use_visitor_id(client):
    registration = client.post("/visitors/register", json=student_data())
    visitor_id = registration.json["visitor"]["id"]
    client.post("/visitors/check-out", json={"visitor_id": visitor_id})

    check_in = client.post("/visitors/check-in", json={
        "visitor_id": visitor_id, "purpose": "Consultation",
    })
    check_out = client.post("/visitors/check-out", json={"visitor_id": visitor_id})

    assert check_in.status_code == 201
    assert check_in.json["visit"]["purpose"] == "Consultation"
    assert check_in.json["visit"]["visitor_id"] == visitor_id
    assert check_out.status_code == 200
    assert check_out.json["visit"]["check_out"] is not None
    assert len(data_access.get_all_records("visit")) == 2


def test_check_in_rejects_existing_active_visit(client):
    registered = client.post("/visitors/register", json=student_data())
    visitor_id = registered.json["visitor"]["id"]

    duplicate = client.post("/visitors/check-in", json={
        "visitor_id": visitor_id, "purpose": "Another visit",
    })

    assert duplicate.status_code == 409
    assert len(data_access.get_all_records("visit")) == 1


@pytest.mark.parametrize("payload", [{}, {"visitor_id": True}, {"visitor_id": -1}])
def test_check_in_rejects_missing_or_invalid_details(client, payload):
    response = client.post("/visitors/check-in", json={"purpose": "Research", **payload})

    assert response.status_code == 400


def test_check_in_unknown_visitor_returns_not_found(client):
    response = client.post("/visitors/check-in", json={
        "visitor_id": 19100001, "purpose": "Research",
    })
    assert response.status_code == 404


def test_check_out_without_active_visit_returns_conflict(client):
    registered = client.post("/visitors/register", json=student_data())
    visitor_id = registered.json["visitor"]["id"]
    client.post("/visitors/check-out", json={"visitor_id": visitor_id})

    response = client.post("/visitors/check-out", json={"visitor_id": visitor_id})

    assert response.status_code == 409


def test_check_out_unknown_visitor_returns_not_found(client):
    response = client.post("/visitors/check-out", json={"visitor_id": 19100001})
    assert response.status_code == 404
