import pytest
from app import data_access
from app.models import Book, ResourceCondition, ResourceStatus


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    return tmp_path



book = Book("Animal Farm", "George Orwell", 6465, "Dystopian")


def test_create_book_model_in_file(temp_data_dir):
    data = book.to_dict()

    record = data_access.create("book", data)
    print(record)

    assert record["id"] == 29200001
    assert record["resource_type"] == "book"
    assert record["name"] == "Animal Farm"


def test_create_record_makes_data_directory(tmp_path, monkeypatch):
    data_dir = tmp_path / "nested" / "data"
    monkeypatch.setattr(data_access, "DB_DIR", data_dir)

    record = data_access.create("visitor", {"name": "Taylor Smith"})

    assert data_dir.is_dir()
    assert data_access.get_all_records("visitor") == [record]


def test_read_book_from_file(temp_data_dir):
    created = data_access.create("book", book.to_dict())

    assert data_access.get_record("book", created["id"]) == created
    assert data_access.get_all_records("book") == [created]


def test_update_book_in_file(temp_data_dir):
    created = data_access.create("book", book.to_dict())

    updated = data_access.update(
        "book",
        created["id"],
        {
            "name": "Animal Farm (updated)",
            "status": ResourceStatus.RESERVED.value,
            "condition": ResourceCondition.DAMAGED.value,
        },
    )

    assert updated is not None
    assert updated["name"] == "Animal Farm (updated)"
    assert updated["status"] == "reserved"
    assert updated["condition"] == "damaged"


def test_delete_book_from_file(temp_data_dir):
    created = data_access.create("book", book.to_dict())

    assert data_access.delete("book", created["id"]) is True
    assert data_access.get_record("book", created["id"]) is None


def test_unknown_file_name_is_rejected():
    with pytest.raises(ValueError):
        data_access.get_all_records("unknown")