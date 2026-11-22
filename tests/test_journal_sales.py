from datetime import date

import pytest

from app import data_access
from app.modules import journal_sales


@pytest.fixture(autouse=True)
def temp_data(tmp_path, monkeypatch):
    # Use a temporary folder so tests never touch the real data files
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)


@pytest.fixture
def journal():
    # Simple mock journal: price 10, stock 5
    return data_access.create(
        "journal",
        {"name": "Social and Economic Studies", "author": "SALISES",
         "price": 10.0, "stock": 5, "status": "available", "condition": "good"},
    )


def test_record_sale_success(journal):
    sale = journal_sales.record_sale(journal["id"], 2, "2026-11-18")

    assert sale["journal_id"] == journal["id"]
    assert sale["quantity"] == 2
    assert sale["sale_amount"] == 20.0
    assert sale["date_sold"] == date(2026, 11, 18)
    assert sale["payment_confirmed"] is False
    assert len(journal_sales.list_sales()) == 1
    # The saved file holds the date as text
    assert journal_sales.list_sales()[0]["date_sold"] == "2026-11-18"


def test_stock_reduced_after_sale(journal):
    journal_sales.record_sale(journal["id"], 2, "2026-11-18")

    assert data_access.get_record("journal", journal["id"])["stock"] == 3


def test_sale_exceeding_stock_rejected(journal):
    with pytest.raises(ValueError):
        journal_sales.record_sale(journal["id"], 6, "2026-11-18")

    assert journal_sales.list_sales() == []
    assert data_access.get_record("journal", journal["id"])["stock"] == 5


def test_stock_restored_if_saving_sale_fails(journal, monkeypatch):
    real_create = data_access.create

    def failing_create(file_name, record):
        if file_name == "sale":
            raise OSError("disk error")
        return real_create(file_name, record)

    monkeypatch.setattr(data_access, "create", failing_create)

    with pytest.raises(OSError):
        journal_sales.record_sale(journal["id"], 2, "2026-11-18")

    assert data_access.get_record("journal", journal["id"])["stock"] == 5
    assert journal_sales.list_sales() == []


def test_sale_of_last_copy_allowed_then_blocked(journal):
    journal_sales.record_sale(journal["id"], 5, "2026-11-18")

    with pytest.raises(ValueError):
        journal_sales.record_sale(journal["id"], 1, "2026-11-18")


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", None, True])
def test_invalid_quantity_rejected(journal, quantity):
    with pytest.raises(ValueError):
        journal_sales.record_sale(journal["id"], quantity, "2026-11-18")

    assert journal_sales.list_sales() == []


@pytest.mark.parametrize("sale_date", [None, "", "18-11-2026", "2026-13-45", 20261118])
def test_missing_or_invalid_date_rejected(journal, sale_date):
    with pytest.raises(ValueError):
        journal_sales.record_sale(journal["id"], 1, sale_date)

    assert journal_sales.list_sales() == []


@pytest.mark.parametrize("journal_id", [None, "abc", 999999])
def test_missing_or_unknown_journal_rejected(journal, journal_id):
    with pytest.raises(ValueError):
        journal_sales.record_sale(journal_id, 1, "2026-11-18")


@pytest.mark.parametrize("price", [0, -5, None, "10"])
def test_invalid_journal_price_rejected(price):
    bad_journal = data_access.create(
        "journal", {"name": "Bad Price", "price": price, "stock": 5}
    )

    with pytest.raises(ValueError):
        journal_sales.record_sale(bad_journal["id"], 1, "2026-11-18")

    assert data_access.get_record("journal", bad_journal["id"])["stock"] == 5


def test_confirm_payment(journal):
    sale = journal_sales.record_sale(journal["id"], 1, "2026-11-18")

    confirmed = journal_sales.confirm_payment(sale["id"])

    assert confirmed["payment_confirmed"] is True


def test_confirm_payment_unknown_sale():
    with pytest.raises(ValueError):
        journal_sales.confirm_payment(999999)


def test_receipt_not_given_before_payment(journal):
    sale = journal_sales.record_sale(journal["id"], 1, "2026-11-18")

    with pytest.raises(ValueError):
        journal_sales.generate_receipt(sale["id"])


def test_receipt_after_payment_confirmed(journal):
    sale = journal_sales.record_sale(journal["id"], 3, "2026-11-18")
    journal_sales.confirm_payment(sale["id"])

    receipt = journal_sales.generate_receipt(sale["id"])

    assert receipt["journal_name"] == "Social and Economic Studies"
    assert receipt["quantity"] == 3
    assert receipt["sale_amount"] == 30.0
    assert receipt["date_sold"] == "2026-11-18"


def test_receipt_unknown_sale():
    with pytest.raises(ValueError):
        journal_sales.generate_receipt(999999)


def test_list_sales_shows_previous_sales(journal):
    journal_sales.record_sale(journal["id"], 1, "2026-11-18")
    journal_sales.record_sale(journal["id"], 2, "2026-11-19")

    sales = journal_sales.list_sales()

    assert [s["quantity"] for s in sales] == [1, 2]
