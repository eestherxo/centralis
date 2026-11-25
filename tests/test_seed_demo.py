from app import data_access
from scripts import seed_demo


def test_demo_seed_populates_frontend_data_and_is_repeatable(tmp_path, monkeypatch):
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)

    seed_demo.main()
    initial_counts = {
        collection: len(data_access.get_all_records(collection))
        for collection in ("user", "visitor", "book", "journal", "room",
                           "archival", "reservation", "visit", "sale", "fine")
    }
    seed_demo.main()
    second_counts = {
        collection: len(data_access.get_all_records(collection))
        for collection in initial_counts
    }

    assert initial_counts == second_counts
    assert initial_counts["user"] == 2
    assert initial_counts["visitor"] == 3
    assert initial_counts["reservation"] == 3
    assert initial_counts["sale"] == 1
    assert initial_counts["fine"] == 2
    assert any(item["status"] == "pending" for item in data_access.get_all_records("reservation"))
    assert any(item["status"] == "unpaid" for item in data_access.get_all_records("fine"))
