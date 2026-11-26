import pytest

from app import data_access
from app.models import ResourceStatus
from app.modules import resource_management


@pytest.fixture(autouse=True)
def temporary_data(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)


def test_create_and_update_resource_records():
    book = resource_management.create_resource("book", {
        "name": "Research Book", "author": "SALISES", "price": 1200,
        "genre": "Research",
    })

    updated = resource_management.update_resource("book", book["id"], {
        "name": "Updated Research Book", "status": "reserved",
    })

    assert book["resource_type"] == "book"
    assert updated["name"] == "Updated Research Book"
    assert updated["status"] == "reserved"


@pytest.mark.parametrize("resource_type", ["book", "journal", "room", "archival"])
def test_create_supported_resource_types(resource_type):
    data = {
        "book": {"name": "Book", "author": "Author", "price": 10, "genre": "Test"},
        "journal": {"name": "Journal", "author": "Author", "price": 10, "stock": 3},
        "room": {"name": "Room", "capacity": 12},
        "archival": {"name": "Archive"},
    }[resource_type]

    record = resource_management.create_resource(resource_type, data)

    assert record["resource_type"] == resource_type
    assert record["status"] == "available"
    assert record["condition"] == "good"


def test_invalid_resource_data_and_update_fields_are_rejected():
    with pytest.raises(ValueError, match="Invalid resource type"):
        resource_management.create_resource("boat", {"name": "Boat"})
    with pytest.raises(ValueError, match="JSON"):
        resource_management.create_resource("book", None)
    book = resource_management.create_resource("book", {
        "name": "Book", "author": "Author", "price": 10, "genre": "Test",
    })
    with pytest.raises(ValueError, match="at least one"):
        resource_management.update_resource("book", book["id"], {})
    with pytest.raises(ValueError, match="cannot be updated"):
        resource_management.update_resource("book", book["id"], {"id": 1})
    with pytest.raises(ValueError, match="Invalid status"):
        resource_management.update_resource("book", book["id"], {"status": "lost"})


def test_update_missing_resource_returns_none():
    assert resource_management.update_resource("book", 29200099, {"name": "Missing"}) is None


def test_available_resources_filter_resource_type_and_condition():
    book = resource_management.create_resource("book", {
        "name": "Available", "author": "Author", "price": 10, "genre": "Test",
    })
    resource_management.create_resource("book", {
        "name": "Hidden", "author": "Author", "price": 10, "genre": "Test",
        "status": ResourceStatus.RESERVED,
    })
    resource_management.create_resource("room", {"name": "Room", "capacity": 2})

    available = resource_management.list_available_resources()
    books = resource_management.list_available_resources("book")

    assert {item["id"] for item in available} == {book["id"], 39300001}
    assert [item["name"] for item in books] == ["Available"]
    with pytest.raises(ValueError, match="Invalid resource type"):
        resource_management.list_available_resources("boat")


def test_resource_with_pending_or_approved_reservation_cannot_be_deleted():
    room = resource_management.create_resource("room", {"name": "Room", "capacity": 5})
    data_access.create("reservation", {
        "visitor_id": 19100001, "resource_id": room["id"],
        "reservation_type": "room", "status": "approved",
        "request_date": "2026-11-01",
    })

    assert resource_management.delete_resource("room", room["id"]) is False
    assert data_access.get_record("room", room["id"]) is not None


def test_declined_reservation_does_not_block_delete():
    book = resource_management.create_resource("book", {
        "name": "Book", "author": "Author", "price": 10, "genre": "Test",
    })
    data_access.create("reservation", {
        "visitor_id": 19100001, "resource_id": book["id"],
        "reservation_type": "book", "status": "declined",
        "request_date": "2026-11-01",
    })

    assert resource_management.delete_resource("book", book["id"]) is True
    assert data_access.get_record("book", book["id"]) is None
