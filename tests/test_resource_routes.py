import pytest

from app import data_access
from app.modules.authentication import create_user
from run import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(
    app.config,
    "JWT_SECRET_KEY",
    "test-secret-key-that-is-long-enough-123",
)

    with app.test_client() as test_client:
        yield test_client

@pytest.fixture
def admin_headers(client):
    _, status = create_user({
        "name": "Test Admin",
        "email": "admin@test.example",
        "password": "test-password-123",
        "role": "admin",
    })
    assert status == 201

    response = client.post(
        "/auth/login",
        json={
            "email": "admin@test.example",
            "password": "test-password-123",
        },
    )
    assert response.status_code == 200

    return {
        "Authorization": f"Bearer {response.json['access_token']}"
    }

def add_book(client, admin_headers):
    return client.post(
        "/inventory/add",
        json={
            "type": "book",
            "data": {
                "name": "Animal Farm",
                "author": "George Orwell",
                "price": 6465,
                "genre": "Dystopian",
            },
        },
        headers=admin_headers
    )


def test_add_book(client, admin_headers):
    response = add_book(client, admin_headers)

    assert response.status_code == 201
    record = response.json["book"]
    assert isinstance(record, dict)
    assert record["id"] is not None
    assert record["resource_type"] == "book"
    assert record["status"] == "available"


def test_invalid_resource_type(client, admin_headers):
    response = client.post(
        "/inventory/add",
        json={"type": "spaceship", "data": {"name": "Enterprise"}},
        headers=admin_headers
    )

    assert response.status_code == 400


def test_update_resource(client, admin_headers):
    created = add_book(client, admin_headers).json["book"]
    resource_id = created["id"]

    response = client.put(
        f"/inventory/book/{resource_id}",
        json={"data": {"status": "reserved"}},
        headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json["book"]["status"] == "reserved"
    assert response.json["book"]["id"] == resource_id

    rejected = client.put(
        f"/inventory/book/{resource_id}",
        json={"data": {"id": 123}},
        headers=admin_headers
    )
    assert rejected.status_code == 400


def test_delete_resource(client, admin_headers):
    created = add_book(client, admin_headers).json["book"]

    response = client.delete(
        f"/inventory/book/{created['id']}", 
        headers=admin_headers
        )

    assert response.status_code == 200
    assert data_access.get_record("book", created["id"]) is None


def test_cannot_delete_resource_with_pending_reservation(client, admin_headers):
    created = add_book(client, admin_headers
    ).json["book"]
    data_access.create(
        "reservation",
        {
            "resource_id": created["id"],
            "reservation_type": "book",
            "status": "pending",
        },
    )

    response = client.delete(
        f"/inventory/book/{created['id']}",
        headers=admin_headers
        )

    assert response.status_code == 409
    assert data_access.get_record("book", created["id"]) is not None


def test_available_endpoint(client, admin_headers):
    first = add_book(client, admin_headers).json["book"]
    second = add_book(client, admin_headers).json["book"]
    third = add_book(client, admin_headers).json["book"]

    client.put(
        f"/inventory/book/{second['id']}",
        json={"data": {"status": "reserved"}},
        headers=admin_headers
    )
    client.put(
        f"/inventory/book/{third['id']}",
        json={"data": {"condition": "damaged"}},
        headers=admin_headers
    )

    response = client.get("/inventory/available?type=book")

    assert response.status_code == 200
    available_ids = {record["id"] for record in response.json["resources"]}
    assert available_ids == {first["id"]}