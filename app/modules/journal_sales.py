from datetime import date

from app import data_access
from app.models import Sale


def record_sale(journal_id, quantity, date_sold):
    # Journal id must be a whole number
    if not isinstance(journal_id, int) or isinstance(journal_id, bool):
        raise ValueError("A valid journal is required")

    # Quantity must be a whole number greater than zero
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValueError("Quantity must be a whole number greater than 0")

    # Sale date must be given as text like "2026-11-18"
    if not isinstance(date_sold, str):
        raise ValueError("A sale date is required")
    try:
        date_sold = date.fromisoformat(date_sold)
    except ValueError:
        raise ValueError("Sale date must be a valid date (YYYY-MM-DD)")

    journal = data_access.get_record("journal", journal_id)
    if journal is None:
        raise ValueError("Journal not found")

    # Price must be a number greater than zero
    price = journal.get("price")
    if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
        raise ValueError("Journal has an invalid price")

    # Cannot sell more than what is in stock
    if quantity > journal["stock"]:
        raise ValueError("Quantity exceeds available stock")

    sale = Sale(
        journal=journal_id,
        quantity=quantity,
        sale_amount=round(price * quantity, 2),
        date_sold=date_sold,
    )

    # Reduce the stock first. update() returns None if the journal was not found
    updated = data_access.update("journal", journal_id, {"stock": journal["stock"] - quantity})
    if updated is None:
        raise ValueError("Journal not found")

    # If saving the sale fails, put the stock back so records stay correct
    try:
        saved_sale = data_access.create("sale", sale.to_dict())
    except Exception:
        data_access.update("journal", journal_id, {"stock": journal["stock"]})
        raise

    return saved_sale


def confirm_payment(sale_id):
    sale = data_access.get_record("sale", sale_id)
    if sale is None:
        raise ValueError("Sale not found")

    return data_access.update("sale", sale_id, {"payment_confirmed": True})


def generate_receipt(sale_id):
    sale = data_access.get_record("sale", sale_id)
    if sale is None:
        raise ValueError("Sale not found")

    # Receipts are only given once staff have confirmed payment
    if not sale.get("payment_confirmed", False):
        raise ValueError("Payment has not been confirmed")

    journal = data_access.get_record("journal", sale["journal_id"])
    if journal is None:
        raise ValueError("Journal not found")

    return {
        "sale_id": sale["id"],
        "journal_name": journal["name"],
        "quantity": sale["quantity"],
        "sale_amount": sale["sale_amount"],
        "date_sold": sale["date_sold"],
    }


def list_sales():
    return data_access.get_all_records("sale")
