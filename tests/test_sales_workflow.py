import pytest

from app import data_access
from app.modules.authentication import create_user
from run import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Real Centralis app from run.py, but with a temporary data folder
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-123")

    with app.test_client() as test_client:
        yield test_client


def login(client, name, role):
    # Create a user with the real auth code, then log in through /auth/login
    create_user({"name": name, "email": f"{name}@test.com",
                 "password": "pass1234", "role": role})
    response = client.post(
        "/auth/login", json={"email": f"{name}@test.com", "password": "pass1234"}
    )
    return {"Authorization": f"Bearer {response.json['access_token']}"}


def add_journal(client, admin):
    # Admin adds a journal through the real inventory route
    response = client.post(
        "/inventory/add",
        json={"type": "journal",
              "data": {"name": "Social and Economic Studies", "author": "SALISES",
                       "price": 10.0, "stock": 5}},
        headers=admin,
    )
    assert response.status_code == 201
    return response.json["journal"]


def sale_data(journal, **changes):
    data = {"journal_id": journal["id"], "quantity": 2, "date_sold": "2026-11-18"}
    data.update(changes)
    return data


def test_full_journal_sale_workflow(client):
    admin = login(client, "admin", "admin")
    staff = login(client, "staff", "staff")
    journal = add_journal(client, admin)

    # Staff records a sale and stock goes down
    response = client.post("/sales", json=sale_data(journal), headers=staff)
    assert response.status_code == 201
    sale = response.json["sale"]
    assert sale["sale_amount"] == 20.0
    assert data_access.get_record("journal", journal["id"])["stock"] == 3

    # Staff can see the saved sale
    sales = client.get("/sales", headers=staff).json["sales"]
    assert [s["id"] for s in sales] == [sale["id"]]

    # No receipt until payment is confirmed
    assert client.get(f"/sales/{sale['id']}/receipt", headers=staff).status_code == 409

    # Confirm payment, then get the receipt
    assert client.post(f"/sales/{sale['id']}/confirm-payment", headers=staff).status_code == 200
    receipt = client.get(f"/sales/{sale['id']}/receipt", headers=staff).json["receipt"]
    assert receipt == {
        "sale_id": sale["id"],
        "journal_name": "Social and Economic Studies",
        "quantity": 2,
        "sale_amount": 20.0,
        "date_sold": "2026-11-18",
    }

    # The admin can use the saved sale in the existing journal sales report
    report = client.post(
        "/reports/generate",
        json={"report_type": "journal_sales",
              "start_date": "2026-11-01", "end_date": "2026-11-30"},
        headers=admin,
    )
    assert report.status_code == 200
    assert report.json["records"] == [{
        "sale_id": sale["id"],
        "journal": "Social and Economic Studies",
        "quantity": 2,
        "sale_date": "2026-11-18",
        "total_amount": 20.0,
    }]


def test_sales_need_login(client):
    assert client.post("/sales", json={}).status_code == 401
    assert client.get("/sales").status_code == 401
    assert client.post("/sales/1/confirm-payment").status_code == 401
    assert client.get("/sales/1/receipt").status_code == 401


def test_invalid_sales_rejected_and_stock_unchanged(client):
    admin = login(client, "admin", "admin")
    staff = login(client, "staff", "staff")
    journal = add_journal(client, admin)

    bad_sales = [
        sale_data(journal, quantity=0),
        sale_data(journal, quantity=6),
        sale_data(journal, date_sold="not-a-date"),
        sale_data(journal, journal_id=999999),
        {"journal_id": journal["id"], "quantity": 1},
    ]
    for bad_sale in bad_sales:
        response = client.post("/sales", json=bad_sale, headers=staff)
        assert response.status_code == 400

    assert data_access.get_all_records("sale") == []
    assert data_access.get_record("journal", journal["id"])["stock"] == 5
