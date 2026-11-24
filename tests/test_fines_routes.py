from datetime import date

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app import data_access
from app.modules import resource_fines
from app.routes.fines import fines_bp


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Temporary data folder and a small test app with only the fines routes
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setattr(resource_fines, "_today", lambda: date(2026, 11, 21))
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-123"
    JWTManager(app)
    app.register_blueprint(fines_bp)

    with app.app_context():
        yield app.test_client()


def login_as(role):
    # Create a test user and return a login header for them
    user = data_access.create(
        "user",
        {"name": "Test User", "email": f"{role}@test.com", "password": "x", "role": role},
    )
    token = create_access_token(identity=str(user["id"]))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff():
    return login_as("staff")


@pytest.fixture
def visitor():
    return data_access.create(
        "visitor",
        {"name": "Ashleigh Brown", "phone_number": "876-555-0101",
         "type": "postgraduate", "purpose": "Research"},
    )


@pytest.fixture
def book():
    return data_access.create(
        "book",
        {"name": "Caribbean Economic Survey", "author": "SALISES", "price": 4500.0,
         "genre": "Economics", "status": "reserved", "condition": "good"},
    )


@pytest.fixture
def loan(visitor, book):
    return data_access.create(
        "reservation",
        {"visitor_id": visitor["id"], "resource_id": book["id"],
         "reservation_type": "book", "status": "approved",
         "request_date": "2026-11-07", "expected_return": "2026-11-14",
         "actual_return": None},
    )


def return_loan(client, headers, loan, return_date="2026-11-17", **extra):
    body = {"reservation_id": loan["id"], "return_date": return_date, **extra}
    return client.post("/fines/returns", json=body, headers=headers)


def test_staff_records_late_return(client, staff, loan):
    response = return_loan(client, staff, loan)

    assert response.status_code == 201
    fine = response.json["fines"][0]
    assert fine["amount"] == 150.0
    assert fine["status"] == "unpaid"
    assert fine["reason"] == "late"


def test_on_time_return_has_no_fine(client, staff, loan):
    response = return_loan(client, staff, loan, "2026-11-12")

    assert response.status_code == 201
    assert response.json["fines"] == []
    assert data_access.get_all_records("fine") == []


def test_admin_can_record_return(client, loan):
    assert return_loan(client, login_as("admin"), loan).status_code == 201


def test_requests_without_login_rejected(client, loan):
    response = client.post("/fines/returns", json={"reservation_id": loan["id"]})

    assert response.status_code == 401
    assert data_access.get_all_records("fine") == []


def test_user_who_does_not_exist_rejected(client, loan):
    token = create_access_token(identity="999999")
    headers = {"Authorization": f"Bearer {token}"}

    response = return_loan(client, headers, loan)

    assert response.status_code == 403
    assert data_access.get_all_records("fine") == []


def test_user_without_staff_role_rejected_everywhere(client, staff, loan, book, visitor):
    outsider = login_as("guest")
    fine = return_loan(client, staff, loan).json["fines"][0]

    attempts = [
        return_loan(client, outsider, loan),
        client.post("/fines/lost-or-damaged", json={"resource_id": book["id"], "condition": "lost"},
                    headers=outsider),
        client.get("/fines", headers=outsider),
        client.get("/fines/loans", headers=outsider),
        client.get("/fines/visitors", headers=outsider),
        client.get("/fines/resources", headers=outsider),
        client.get(f"/fines/visitor/{visitor['id']}/unpaid", headers=outsider),
        client.post(f"/fines/{fine['id']}/confirm-payment", headers=outsider),
        client.get(f"/fines/{fine['id']}/receipt", headers=outsider),
    ]

    assert [r.status_code for r in attempts] == [403] * len(attempts)
    # nothing changed: the one fine is still unpaid
    assert data_access.get_record("fine", fine["id"])["status"] == "unpaid"


def test_missing_or_bad_input_rejected(client, staff, loan):
    assert client.post("/fines/returns", headers=staff).status_code == 400
    assert return_loan(client, staff, loan, "not-a-date").status_code == 400
    assert return_loan(client, staff, loan, condition="lost").status_code == 400
    assert client.post("/fines/returns", json={"reservation_id": 69699999},
                       headers=staff).status_code == 404


def test_lost_resource_fine(client, staff, loan, book, visitor):
    response = client.post(
        "/fines/lost-or-damaged",
        json={"resource_id": book["id"], "condition": "lost"},
        headers=staff,
    )

    assert response.status_code == 201
    assert response.json["fine"]["amount"] == 4500.0
    assert response.json["fine"]["visitor_id"] == visitor["id"]
    assert data_access.get_record("book", book["id"])["condition"] == "lost"


def test_staff_names_the_responsible_borrower(client, staff, visitor):
    book = data_access.create(
        "book",
        {"name": "Spare Copy", "author": "SALISES", "price": 3000.0, "genre": "Economics",
         "status": "available", "condition": "good"},
    )

    response = client.post(
        "/fines/lost-or-damaged",
        json={"resource_id": book["id"], "condition": "damaged", "visitor_id": visitor["id"]},
        headers=staff,
    )

    assert response.status_code == 201
    assert response.json["fine"]["reason"] == "damaged"


def test_lost_resource_without_borrower_rejected(client, staff):
    book = data_access.create(
        "book",
        {"name": "Spare Copy", "author": "SALISES", "price": 3000.0, "genre": "Economics",
         "status": "available", "condition": "good"},
    )

    response = client.post("/fines/lost-or-damaged",
                           json={"resource_id": book["id"], "condition": "lost"}, headers=staff)

    assert response.status_code == 400


def test_view_unpaid_fines_for_a_visitor(client, staff, loan, visitor):
    return_loan(client, staff, loan)

    response = client.get(f"/fines/visitor/{visitor['id']}/unpaid", headers=staff)

    assert response.status_code == 200
    fines = response.json["fines"]
    assert len(fines) == 1
    assert fines[0]["amount"] == 150.0
    assert fines[0]["resource_name"] == "Caribbean Economic Survey"
    assert fines[0]["reason"] == "late"
    assert fines[0]["date_issued"] == "2026-11-21"


def test_unpaid_fines_for_unknown_visitor(client, staff):
    assert client.get("/fines/visitor/19100099/unpaid", headers=staff).status_code == 404


def test_list_fines_with_status_filter(client, staff, loan):
    return_loan(client, staff, loan)

    assert len(client.get("/fines", headers=staff).json["fines"]) == 1
    assert len(client.get("/fines?status=unpaid", headers=staff).json["fines"]) == 1
    assert client.get("/fines?status=paid", headers=staff).json["fines"] == []
    assert client.get("/fines?status=bogus", headers=staff).status_code == 400


def test_pickers_for_active_loans_visitors_and_resources(client, staff, loan):
    loans = client.get("/fines/loans", headers=staff).json["loans"]
    visitors = client.get("/fines/visitors", headers=staff).json["visitors"]
    resources = client.get("/fines/resources", headers=staff).json["resources"]

    assert loans[0]["days_late"] == 7 and loans[0]["fine_so_far"] == 350.0
    assert visitors[0]["name"] == "Ashleigh Brown"
    assert resources[0]["price"] == 4500.0


def test_confirm_payment_then_receipt(client, staff, loan):
    fine = return_loan(client, staff, loan).json["fines"][0]

    paid = client.post(f"/fines/{fine['id']}/confirm-payment", headers=staff)
    assert paid.status_code == 200
    assert paid.json["fine"]["status"] == "paid"
    assert paid.json["fine"]["date_paid"] == "2026-11-21"

    receipt = client.get(f"/fines/{fine['id']}/receipt", headers=staff)
    assert receipt.status_code == 200
    assert receipt.mimetype == "application/pdf"
    assert receipt.data.startswith(b"%PDF")
    assert b"Ashleigh Brown" in receipt.data


def test_no_receipt_for_unpaid_fine(client, staff, loan):
    fine = return_loan(client, staff, loan).json["fines"][0]

    assert client.get(f"/fines/{fine['id']}/receipt", headers=staff).status_code == 409


def test_paying_twice_or_unknown_fine(client, staff, loan):
    fine = return_loan(client, staff, loan).json["fines"][0]
    client.post(f"/fines/{fine['id']}/confirm-payment", headers=staff)

    assert client.post(f"/fines/{fine['id']}/confirm-payment", headers=staff).status_code == 400
    assert client.post("/fines/79799999/confirm-payment", headers=staff).status_code == 404
    assert client.get("/fines/79799999/receipt", headers=staff).status_code == 404
