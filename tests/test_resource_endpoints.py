import pytest

from app import data_access
from run import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    monkeypatch.setitem(app.config, "TESTING", True)

    with app.test_client() as test_client:
        yield test_client


def add_book(client):
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
    )


def test_add_book(client):
    response = add_book(client)

    assert response.status_code == 201
    record = response.json["book"]
    assert isinstance(record, dict)
    assert record["id"] is not None
    assert record["resource_type"] == "book"
    assert record["status"] == "available"


def test_invalid_resource_type(client):
    response = client.post(
        "/inventory/add",
        json={"type": "spaceship", "data": {"name": "Enterprise"}},
    )

    assert response.status_code == 400


def test_update_resource(client):
    created = add_book(client).json["book"]
    resource_id = created["id"]

    response = client.put(
        f"/inventory/book/{resource_id}",
        json={"data": {"status": "reserved"}},
    )

    assert response.status_code == 200
    assert response.json["book"]["status"] == "reserved"
    assert response.json["book"]["id"] == resource_id

    rejected = client.put(
        f"/inventory/book/{resource_id}",
        json={"data": {"id": 123}},
    )
    assert rejected.status_code == 400


def test_delete_resource(client):
    created = add_book(client).json["book"]

    response = client.delete(f"/inventory/book/{created['id']}")

    assert response.status_code == 200
    assert data_access.get_record("book", created["id"]) is None


def test_cannot_delete_resource_with_pending_reservation(client):
    created = add_book(client).json["book"]
    data_access.create(
        "reservation",
        {
            "resource_id": created["id"],
            "reservation_type": "book",
            "status": "pending",
        },
    )

    response = client.delete(f"/inventory/book/{created['id']}")

    assert response.status_code == 409
    assert data_access.get_record("book", created["id"]) is not None


def test_available_endpoint(client):
    first = add_book(client).json["book"]
    second = add_book(client).json["book"]
    third = add_book(client).json["book"]

    client.put(
        f"/inventory/book/{second['id']}",
        json={"data": {"status": "reserved"}},
    )
    client.put(
        f"/inventory/book/{third['id']}",
        json={"data": {"condition": "damaged"}},
    )

    response = client.get("/inventory/available?type=book")

    assert response.status_code == 200
    available_ids = {record["id"] for record in response.json["resources"]}
    assert available_ids == {first["id"]}