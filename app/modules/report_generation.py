"""Business logic for generating and exporting administrative reports."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app import data_access


NO_DATA_MESSAGE = "No data available"


def _parse_date(value: Any) -> date:
    """Convert a stored ISO date or timestamp to a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).date()
            except ValueError as exc:
                raise ValueError(
                    "Dates must use the YYYY-MM-DD format"
                ) from exc
    raise ValueError("Dates must use the YYYY-MM-DD format")


def _validate_date_range(start_date: Any, end_date: Any) -> tuple[date, date]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("The start date cannot be later than the end date")
    return start, end


def _required(record: dict[str, Any], field: str) -> Any:
    if field not in record:
        raise ValueError(f"Missing required field: {field}")
    return record[field]


def _records_in_range(
    records: Iterable[dict[str, Any]],
    date_field: str,
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if start <= _parse_date(_required(record, date_field)) <= end
    ]


def _report_result(
    report_type: str,
    start: date,
    end: date,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    report = {
        "report_type": report_type,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "records": records,
    }
    if not records:
        report["message"] = NO_DATA_MESSAGE
    return report


def generate_visitor_report(
    visits: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report visitor details, visit dates, and visit frequency."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(visits, "check_in", start, end)

    visitors: dict[Any, dict[str, Any]] = {}
    for visit in matching:
        visitor_id = _required(visit, "visitor_id")
        if visitor_id not in visitors:
            visitors[visitor_id] = {
                "visitor_id": visitor_id,
                "name": _required(visit, "name"),
                "type": _required(visit, "type"),
                "visit_dates": [],
                "visit_frequency": 0,
            }
        visitors[visitor_id]["visit_dates"].append(
            _parse_date(visit["check_in"]).isoformat()
        )
        visitors[visitor_id]["visit_frequency"] += 1

    report_records = list(visitors.values())
    for visitor in report_records:
        visitor["visit_dates"].sort()
    report_records.sort(key=lambda item: (item["name"], item["visitor_id"]))
    return _report_result("visitor", start, end, report_records)


def generate_reservation_report(
    reservations: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report reservation records using their stored field names."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(reservations, "request_date", start, end)
    fields = ("id", "visitor_id", "resource_id", "request_date", "status")
    report_records = [
        {
            field: (
                record.get("id")
                if field == "id"
                else _parse_date(_required(record, field)).isoformat()
                if field == "request_date"
                else _required(record, field)
            )
            for field in fields
        }
        for record in matching
    ]
    report_records.sort(
        key=lambda item: (item["request_date"], item["id"] or "")
    )
    return _report_result("reservation", start, end, report_records)


def generate_journal_sales_report(
    sales: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report journal sales using date_sold and sale_amount directly."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(sales, "date_sold", start, end)
    fields = ("id", "journal_id", "quantity", "date_sold", "sale_amount")
    report_records = [
        {
            field: (
                record.get("id")
                if field == "id"
                else _parse_date(_required(record, field)).isoformat()
                if field == "date_sold"
                else _required(record, field)
            )
            for field in fields
        }
        for record in matching
    ]
    report_records.sort(key=lambda item: (item["date_sold"], item["id"] or ""))
    return _report_result("journal_sales", start, end, report_records)


def generate_fines_report(
    fines: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report fines using the fields stored by the Fine model."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(fines, "date_issued", start, end)
    fields = (
        "id",
        "visitor_id",
        "reason",
        "amount",
        "resource_id",
        "date_issued",
        "status",
    )
    report_records = [
        {
            field: (
                record.get("id")
                if field == "id"
                else _parse_date(_required(record, field)).isoformat()
                if field == "date_issued"
                else _required(record, field)
            )
            for field in fields
        }
        for record in matching
    ]
    report_records.sort(
        key=lambda item: (item["date_issued"], item["id"] or "")
    )
    return _report_result("fines", start, end, report_records)


ReportGenerator = Callable[
    [Iterable[dict[str, Any]], Any, Any], dict[str, Any]
]

REPORT_GENERATORS: dict[str, ReportGenerator] = {
    "visitor": generate_visitor_report,
    "reservation": generate_reservation_report,
    "journal_sales": generate_journal_sales_report,
    "fines": generate_fines_report,
}

REPORT_EXPORT_COLUMNS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "visitor": (
        "Visitor Report",
        [
            ("visitor_id", "Visitor ID"),
            ("name", "Visitor Name"),
            ("type", "Visitor Type"),
            ("visit_dates", "Visit Dates"),
            ("visit_frequency", "Visit Frequency"),
        ],
    ),
    "reservation": (
        "Reservation Report",
        [
            ("id", "Reservation ID"),
            ("visitor_id", "Visitor ID"),
            ("resource_id", "Resource ID"),
            ("request_date", "Request Date"),
            ("status", "Status"),
        ],
    ),
    "journal_sales": (
        "Journal Sales Report",
        [
            ("id", "Sale ID"),
            ("journal_id", "Journal ID"),
            ("quantity", "Quantity"),
            ("date_sold", "Date Sold"),
            ("sale_amount", "Sale Amount"),
        ],
    ),
    "fines": (
        "Fines Report",
        [
            ("id", "Fine ID"),
            ("visitor_id", "Visitor ID"),
            ("reason", "Reason"),
            ("amount", "Amount"),
            ("resource_id", "Resource ID"),
            ("date_issued", "Date Issued"),
            ("status", "Status"),
        ],
    ),
}


def get_report_records(report_type: str) -> list[dict[str, Any]]:
    """Read report records from the application's JSON data store."""
    if report_type not in REPORT_GENERATORS:
        raise ValueError("A valid report type must be selected")

    if report_type == "visitor":
        visitors = {
            visitor["id"]: visitor
            for visitor in data_access.get_all_records("visitor")
            if visitor.get("id") is not None
        }
        records = []
        for visit in data_access.get_all_records("visit"):
            visitor = visitors.get(visit.get("visitor_id"), {})
            record = dict(visit)
            record["name"] = visitor.get("name", "Unknown")
            record["type"] = visitor.get("type", "Unknown")
            records.append(record)
        return records

    storage_name = {
        "reservation": "reservation",
        "journal_sales": "sale",
        "fines": "fine",
    }[report_type]
    return data_access.get_all_records(storage_name)


def generate_report(
    report_type: str | None,
    records: Iterable[dict[str, Any]],
    start_date: Any,
    end_date: Any,
    role: str | None,
) -> dict[str, Any]:
    """Authorize the user, validate the report type, and generate a report."""
    if not role:
        raise PermissionError("Administrator login is required")
    if role.strip().lower() not in {"admin", "administrator"}:
        raise PermissionError("Only an Administrator may access reports")
    if not report_type or report_type not in REPORT_GENERATORS:
        raise ValueError("A valid report type must be selected")
    return REPORT_GENERATORS[report_type](records, start_date, end_date)


def _excel_cell_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)
    return value


def export_report_to_excel(
    report: dict[str, Any], output_path: str | Path
) -> Path:
    """Export a generated report to a Microsoft Excel .xlsx file."""
    report_type = report.get("report_type")
    if report_type not in REPORT_EXPORT_COLUMNS:
        raise ValueError("The report type cannot be exported to Microsoft Excel")
    if "start_date" not in report or "end_date" not in report:
        raise ValueError("The report must include a start date and an end date")

    output_file = Path(output_path)
    if output_file.suffix.lower() != ".xlsx":
        output_file = output_file.with_suffix(".xlsx")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    title, columns = REPORT_EXPORT_COLUMNS[report_type]
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = title[:31]
    last_column = get_column_letter(len(columns))

    worksheet.merge_cells(f"A1:{last_column}1")
    worksheet["A1"] = title
    worksheet["A1"].font = Font(size=18, bold=True, color="FFFFFF")
    worksheet["A1"].fill = PatternFill("solid", fgColor="123F68")
    worksheet["A1"].alignment = Alignment(horizontal="center")

    worksheet.merge_cells(f"A2:{last_column}2")
    worksheet["A2"] = (
        f"Date range: {report['start_date']} to {report['end_date']}"
    )
    worksheet["A2"].font = Font(italic=True)
    worksheet["A2"].alignment = Alignment(horizontal="center")

    records = report.get("records", [])
    if not records:
        worksheet.merge_cells(f"A4:{last_column}4")
        worksheet["A4"] = report.get("message", NO_DATA_MESSAGE)
        worksheet["A4"].alignment = Alignment(horizontal="center")
    else:
        for index, (_, heading) in enumerate(columns, start=1):
            cell = worksheet.cell(row=4, column=index, value=heading)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="155C94")
            cell.alignment = Alignment(horizontal="center")

        for row_index, record in enumerate(records, start=5):
            for column_index, (field, _) in enumerate(columns, start=1):
                cell = worksheet.cell(
                    row=row_index,
                    column=column_index,
                    value=_excel_cell_value(record.get(field)),
                )
                if field in {"amount", "sale_amount"}:
                    cell.number_format = "#,##0.00"

        worksheet.auto_filter.ref = f"A4:{last_column}{worksheet.max_row}"
        worksheet.freeze_panes = "A5"

    for column_index, (field, heading) in enumerate(columns, start=1):
        values = [heading]
        values.extend(_excel_cell_value(record.get(field)) for record in records)
        longest = max(len(str(value)) for value in values)
        worksheet.column_dimensions[get_column_letter(column_index)].width = min(
            max(longest + 4, 14), 40
        )

    workbook.save(output_file)
    return output_file
