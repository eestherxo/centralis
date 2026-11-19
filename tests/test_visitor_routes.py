from datetime import datetime

import pytest
from flask import Flask

from app import data_access
from app.routes.visitors import visitors_bp


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    app = Flask(__name__)
    app.register_blueprint(visitors_bp)
    return app.test_client()


def visitor_data(**overrides):
    data = {
        "name": "Taylor Smith",
        "phone_number": "555-0123",
        "id_number": "ID-123",
        "faculty": "Science",
        "purpose": "Research",
        "type": "undergraduate",
    }
    data.update(overrides)
    return data


def test_registration_saves_visitor_and_initial_check_in(client):
    response = client.post("/visitors/register", json=visitor_data())

    assert response.status_code == 201
    body = response.get_json()
    assert body["message"] == "Visitor registered and checked in successfully."
    assert body["visitor"]["id_number"] == "ID-123"
    assert datetime.fromisoformat(body["visit"]["check_in"])
    assert body["visit"]["check_out"] is None


def test_registration_rejects_missing_and_invalid_fields(client):
    missing = client.post(
        "/visitors/register", json=visitor_data(phone_number=" ")
    )
    invalid_type = client.post(
        "/visitors/register", json=visitor_data(type="invalid")
    )

    assert missing.status_code == 400
    assert "phone_number" in missing.get_json()["fields"]
    assert invalid_type.status_code == 400
    assert "type" in invalid_type.get_json()["fields"]
    assert data_access.get_all_records("visitor") == []


def test_duplicate_registration_is_rejected(client):
    client.post("/visitors/register", json=visitor_data())

    response = client.post(
        "/visitors/register", json=visitor_data(id_number=" id-123 ")
    )

    assert response.status_code == 409
    assert len(data_access.get_all_records("visitor")) == 1


def test_check_in_and_check_out_create_visit_timestamps(client):
    registration = client.post("/visitors/register", json=visitor_data())
    visitor_id = registration.get_json()["visitor"]["id"]
    initial_visit_id = registration.get_json()["visit"]["id"]
    client.post(
        "/visitors/check-out", json={"id_number": "ID-123"}
    )

    check_in = client.post(
        "/visitors/check-in",
        json={"id_number": "ID-123", "purpose": "Consultation"},
    )
    check_out = client.post(
        "/visitors/check-out", json={"id_number": "ID-123"}
    )

    assert check_in.status_code == 201
    assert check_in.get_json()["visit"]["visitor_id"] == visitor_id
    assert check_in.get_json()["visit"]["purpose"] == "Consultation"
    assert datetime.fromisoformat(check_in.get_json()["visit"]["check_in"])
    assert check_out.status_code == 200
    assert datetime.fromisoformat(check_out.get_json()["visit"]["check_out"])
    assert data_access.get_record("visit", initial_visit_id)["check_out"] is not None
    assert len(data_access.get_all_records("visit")) == 2


def test_check_in_is_rejected_while_previous_visit_is_active(client):
    client.post("/visitors/register", json=visitor_data())

    response = client.post(
        "/visitors/check-in",
        json={"id_number": "ID-123", "purpose": "Another visit"},
    )

    assert response.status_code == 409
    assert len(data_access.get_all_records("visit")) == 1


def test_check_out_without_active_check_in_is_rejected(client):
    client.post("/visitors/register", json=visitor_data())
    client.post("/visitors/check-out", json={"id_number": "ID-123"})

    response = client.post(
        "/visitors/check-out", json={"id_number": "ID-123"}
    )

    assert response.status_code == 409
    assert len(data_access.get_all_records("visit")) == 1
