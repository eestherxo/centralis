import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app import data_access
from app.routes.sales import sales_bp


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Temporary data folder and a small test app with only the sales routes
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-123"
    JWTManager(app)
    app.register_blueprint(sales_bp)

    with app.app_context():
        yield app.test_client()


def login_as(role):
    # Create a mock user and return a login header for them
    user = data_access.create(
        "user",
        {"name": "Test User", "email": f"{role}@test.com",
         "password": "x", "role": role},
    )
    token = create_access_token(identity=str(user["id"]))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff():
    return login_as("staff")


@pytest.fixture
def journal():
    return data_access.create(
        "journal",
        {"name": "Social and Economic Studies", "author": "SALISES",
         "price": 10.0, "stock": 5, "status": "available", "condition": "good"},
    )


def sale_data(journal, **changes):
    data = {"journal_id": journal["id"], "quantity": 2, "date_sold": "2026-11-18"}
    data.update(changes)
    return data


def test_staff_records_sale(client, staff, journal):
    response = client.post("/sales", json=sale_data(journal), headers=staff)

    assert response.status_code == 201
    sale = response.json["sale"]
    assert sale["quantity"] == 2
    assert sale["sale_amount"] == 20.0
    assert sale["date_sold"] == "2026-11-18"
    assert sale["payment_confirmed"] is False
    assert data_access.get_record("journal", journal["id"])["stock"] == 3


def test_admin_records_sale(client, journal):
    admin = login_as("admin")

    response = client.post("/sales", json=sale_data(journal), headers=admin)

    assert response.status_code == 201


def test_sale_without_login_rejected(client, journal):
    response = client.post("/sales", json=sale_data(journal))

    assert response.status_code == 401
    assert data_access.get_all_records("sale") == []


def test_user_who_does_not_exist_rejected(client, journal):
    token = create_access_token(identity="999999")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/sales", json=sale_data(journal), headers=headers)

    assert response.status_code == 403
    assert data_access.get_all_records("sale") == []


def test_missing_information_rejected(client, staff, journal):
    response = client.post(
        "/sales", json={"journal_id": journal["id"], "quantity": 2}, headers=staff
    )

    assert response.status_code == 400
    assert "date" in response.json["error"].lower()
    assert data_access.get_all_records("sale") == []


def test_missing_body_rejected(client, staff):
    response = client.post("/sales", headers=staff)

    assert response.status_code == 400


def test_invalid_quantity_rejected(client, staff, journal):
    response = client.post(
        "/sales", json=sale_data(journal, quantity=0), headers=staff
    )

    assert response.status_code == 400
    assert data_access.get_all_records("sale") == []


def test_sale_over_stock_rejected(client, staff, journal):
    response = client.post(
        "/sales", json=sale_data(journal, quantity=6), headers=staff
    )

    assert response.status_code == 400
    assert data_access.get_all_records("sale") == []
    assert data_access.get_record("journal", journal["id"])["stock"] == 5


def test_confirm_payment_then_receipt(client, staff, journal):
    sale = client.post("/sales", json=sale_data(journal), headers=staff).json["sale"]

    confirm = client.post(f"/sales/{sale['id']}/confirm-payment", headers=staff)
    receipt = client.get(f"/sales/{sale['id']}/receipt", headers=staff)

    assert confirm.status_code == 200
    assert confirm.json["sale"]["payment_confirmed"] is True

    # The receipt is a downloadable PDF with the correct sale details
    assert receipt.status_code == 200
    assert receipt.mimetype == "application/pdf"
    assert f"receipt-{sale['id']}.pdf" in receipt.headers["Content-Disposition"]
    assert "attachment" in receipt.headers["Content-Disposition"]
    assert receipt.data.startswith(b"%PDF")
    assert receipt.data.rstrip().endswith(b"%%EOF")
    assert b"/Count 1" in receipt.data  # one page
    for text in [str(sale["id"]), "Social and Economic Studies", "2",
                 "$20.00", "2026-11-18"]:
        assert text.encode() in receipt.data


def test_receipt_before_payment_rejected(client, staff, journal):
    sale = client.post("/sales", json=sale_data(journal), headers=staff).json["sale"]

    response = client.get(f"/sales/{sale['id']}/receipt", headers=staff)

    assert response.status_code == 409
    assert "receipt" not in response.json


def test_receipt_for_user_who_does_not_exist_rejected(client, staff, journal):
    sale = client.post("/sales", json=sale_data(journal), headers=staff).json["sale"]
    client.post(f"/sales/{sale['id']}/confirm-payment", headers=staff)
    token = create_access_token(identity="999999")

    response = client.get(
        f"/sales/{sale['id']}/receipt", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert not response.data.startswith(b"%PDF")


def test_unknown_sale_returns_404(client, staff):
    confirm = client.post("/sales/999999/confirm-payment", headers=staff)
    receipt = client.get("/sales/999999/receipt", headers=staff)

    assert confirm.status_code == 404
    assert receipt.status_code == 404


def test_receipt_and_confirm_need_login(client, staff, journal):
    sale = client.post("/sales", json=sale_data(journal), headers=staff).json["sale"]

    confirm = client.post(f"/sales/{sale['id']}/confirm-payment")
    receipt = client.get(f"/sales/{sale['id']}/receipt")

    assert confirm.status_code == 401
    assert receipt.status_code == 401


def test_list_previous_sales(client, staff, journal):
    client.post("/sales", json=sale_data(journal, quantity=1), headers=staff)
    client.post("/sales", json=sale_data(journal, quantity=2), headers=staff)

    response = client.get("/sales", headers=staff)

    assert response.status_code == 200
    assert [s["quantity"] for s in response.json["sales"]] == [1, 2]


def test_list_sales_needs_login(client):
    response = client.get("/sales")

    assert response.status_code == 401
