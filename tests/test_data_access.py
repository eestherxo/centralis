import pytest
from app import data_access


# Replaces the DB_DIR with a temporary directory for testing
@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    return tmp_path


def test_create_and_read_record(temp_data_dir):
    assert data_access.create("books", {"name": "Dune"}) is True

    records = data_access.get_all_records("books")
    assert len(records) == 1
    assert records[0]["id"] == 1960001
    assert records[0]["name"] == "Dune"
    assert data_access.get_record("books", 1960001) == records[0]


def test_update_record(temp_data_dir):
    data_access.create("books", {"name": "Dune"})

    updated = data_access.update("books", 1960001, {"name": "Dune Messiah"})

    assert updated is not None
    assert updated["name"] == "Dune Messiah"
    record = data_access.get_record("books", 1960001)
    assert record is not None
    assert record["name"] == "Dune Messiah"


def test_delete_record(temp_data_dir):
    data_access.create("books", {"name": "Dune"})

    assert data_access.delete("books", 1960001) is True
    assert data_access.get_record("books", 1960001) is None
    assert data_access.delete("books", 1960001) is False


def test_unknown_file_name_is_rejected():
    with pytest.raises(ValueError):
        data_access.get_all_records("unknown")
