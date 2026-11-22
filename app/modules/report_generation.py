"""Connect report generation to the application's JSON data store."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app import data_access


SUPPORTED_REPORT_TYPES = {"visitor", "reservation", "journal_sales", "fines"}
RESOURCE_TYPES = ("book", "room", "journal", "archival")


def _date_value(value: Any) -> Any:
    """Return the date part of stored date or timestamp values."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value.split("T", 1)[0].split(" ", 1)[0]
    return value


def _record_index(file_name: str) -> dict[Any, dict[str, Any]]:
    return {
        record.get("id"): record
        for record in data_access.get_all_records(file_name)
        if record.get("id") is not None
    }


def _resource_index() -> dict[Any, dict[str, Any]]:
    resources: dict[Any, dict[str, Any]] = {}
    for resource_type in RESOURCE_TYPES:
        resources.update(_record_index(resource_type))
    return resources


def _name(record: dict[str, Any] | None, fallback: Any) -> str:
    if record and record.get("name"):
        return str(record["name"])
    return str(fallback)


def _visitor_report_records() -> list[dict[str, Any]]:
    visitors = _record_index("visitor")
    records = []
    for visit in data_access.get_all_records("visit"):
        visitor_id = visit.get("visitor_id")
        visitor = visitors.get(visitor_id)
        records.append(
            {
                "visitor_id": visitor_id,
                "visitor_name": _name(visitor, visitor_id),
                "visitor_type": (
                    visitor.get("type", "Unknown") if visitor else "Unknown"
                ),
                "visit_date": _date_value(visit.get("check_in")),
            }
        )
    return records


def _reservation_report_records() -> list[dict[str, Any]]:
    visitors = _record_index("visitor")
    resources = _resource_index()
    records = []
    for reservation in data_access.get_all_records("reservation"):
        visitor_id = reservation.get("visitor_id", reservation.get("visitor"))
        resource_id = reservation.get("resource_id", reservation.get("resource"))
        records.append(
            {
                "reservation_id": reservation.get("id"),
                "visitor": _name(visitors.get(visitor_id), visitor_id),
                "resource": _name(resources.get(resource_id), resource_id),
                "reservation_date": _date_value(
                    reservation.get("reserve_date")
                    or reservation.get("reservation_date")
                    or reservation.get("request_date")
                ),
                "status": reservation.get("status"),
            }
        )
    return records


def _journal_sales_report_records() -> list[dict[str, Any]]:
    journals = _record_index("journal")
    records = []
    for sale in data_access.get_all_records("sale"):
        journal_id = sale.get("journal_id", sale.get("journal"))
        records.append(
            {
                "sale_id": sale.get("id"),
                "journal": _name(journals.get(journal_id), journal_id),
                "quantity": sale.get("quantity"),
                "sale_date": _date_value(
                    sale.get("date_sold") or sale.get("sale_date")
                ),
                "total_amount": sale.get(
                    "sale_amount", sale.get("total_amount")
                ),
            }
        )
    return records


def _fines_report_records() -> list[dict[str, Any]]:
    visitors = _record_index("visitor")
    resources = _resource_index()
    records = []
    for fine in data_access.get_all_records("fine"):
        visitor_id = fine.get("visitor_id", fine.get("visitor"))
        resource_id = fine.get("resource_id", fine.get("resource"))
        records.append(
            {
                "fine_id": fine.get("id"),
                "visitor": _name(visitors.get(visitor_id), visitor_id),
                "fine_type": fine.get("reason", fine.get("fine_type")),
                "amount": fine.get("amount"),
                "resource": _name(resources.get(resource_id), resource_id),
                "date_issued": _date_value(fine.get("date_issued")),
                "payment_status": fine.get(
                    "status", fine.get("payment_status")
                ),
            }
        )
    return records


REPORT_RECORD_PROVIDERS = {
    "visitor": _visitor_report_records,
    "reservation": _reservation_report_records,
    "journal_sales": _journal_sales_report_records,
    "fines": _fines_report_records,
}


def get_report_records(report_type: str) -> list[dict[str, Any]]:
    """Return stored records in the format required by a report generator."""
    if report_type not in SUPPORTED_REPORT_TYPES:
        raise ValueError("A valid report type must be selected")
    return REPORT_RECORD_PROVIDERS[report_type]()
