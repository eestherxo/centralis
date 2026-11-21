"""Report generation for SALISES User Story 03.

The reporting functions accept stored records as dictionaries and return a
consistent report dictionary.  They do not depend on a particular database,
which allows the module to be connected to the group's shared data-access
layer once the remaining record formats have been agreed.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


NO_DATA_MESSAGE = "No data available"


def _parse_date(value: Any) -> date:
    """Convert an ISO date value to a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Dates must use the YYYY-MM-DD format") from exc
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
    matches = []
    for record in records:
        record_date = _parse_date(_required(record, date_field))
        if start <= record_date <= end:
            matches.append(record)
    return matches


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
    """Report registered visitors, visitor types, dates and visit frequency.

    Each visit record requires visitor_id, visitor_name, visitor_type and
    visit_date.  Multiple visits by the same visitor are combined.
    """
    start, end = _validate_date_range(start_date, end_date)
    matching_visits = _records_in_range(visits, "visit_date", start, end)

    visitors: dict[Any, dict[str, Any]] = {}
    for visit in matching_visits:
        visitor_id = _required(visit, "visitor_id")
        if visitor_id not in visitors:
            visitors[visitor_id] = {
                "visitor_id": visitor_id,
                "visitor_name": _required(visit, "visitor_name"),
                "visitor_type": _required(visit, "visitor_type"),
                "visit_dates": [],
                "visit_frequency": 0,
            }

        visitor = visitors[visitor_id]
        visitor["visit_dates"].append(_parse_date(visit["visit_date"]).isoformat())
        visitor["visit_frequency"] += 1

    report_records = list(visitors.values())
    for visitor in report_records:
        visitor["visit_dates"].sort()
    report_records.sort(key=lambda item: (item["visitor_name"], item["visitor_id"]))
    return _report_result("visitor", start, end, report_records)


def generate_reservation_report(
    reservations: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report requested resources, reservation dates and statuses."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(
        reservations, "reservation_date", start, end
    )

    report_records = []
    for reservation in matching:
        item = {
            "visitor": _required(reservation, "visitor"),
            "resource": _required(reservation, "resource"),
            "reservation_date": _parse_date(
                reservation["reservation_date"]
            ).isoformat(),
            "status": _required(reservation, "status"),
        }
        if "reservation_id" in reservation:
            item["reservation_id"] = reservation["reservation_id"]
        report_records.append(item)

    report_records.sort(
        key=lambda item: (item["reservation_date"], item.get("reservation_id", ""))
    )
    return _report_result("reservation", start, end, report_records)


def generate_journal_sales_report(
    sales: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report journals sold, quantities, dates and transaction totals."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(sales, "sale_date", start, end)

    report_records = []
    for sale in matching:
        item = {
            "journal": _required(sale, "journal"),
            "quantity": _required(sale, "quantity"),
            "sale_date": _parse_date(sale["sale_date"]).isoformat(),
            "total_amount": _required(sale, "total_amount"),
        }
        if "sale_id" in sale:
            item["sale_id"] = sale["sale_id"]
        report_records.append(item)

    report_records.sort(
        key=lambda item: (item["sale_date"], item.get("sale_id", ""))
    )
    return _report_result("journal_sales", start, end, report_records)


def generate_fines_report(
    fines: Iterable[dict[str, Any]], start_date: Any, end_date: Any
) -> dict[str, Any]:
    """Report visitors, fine types, amounts, resources and dates issued."""
    start, end = _validate_date_range(start_date, end_date)
    matching = _records_in_range(fines, "date_issued", start, end)

    report_records = []
    for fine in matching:
        item = {
            "visitor": _required(fine, "visitor"),
            "fine_type": _required(fine, "fine_type"),
            "amount": _required(fine, "amount"),
            "resource": _required(fine, "resource"),
            "date_issued": _parse_date(fine["date_issued"]).isoformat(),
            "payment_status": _required(fine, "payment_status"),
        }
        if "fine_id" in fine:
            item["fine_id"] = fine["fine_id"]
        report_records.append(item)

    report_records.sort(
        key=lambda item: (item["date_issued"], item.get("fine_id", ""))
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
            ("visitor_name", "Visitor Name"),
            ("visitor_type", "Visitor Type"),
            ("visit_dates", "Visit Dates"),
            ("visit_frequency", "Visit Frequency"),
        ],
    ),
    "reservation": (
        "Reservation Report",
        [
            ("reservation_id", "Reservation ID"),
            ("visitor", "Visitor"),
            ("resource", "Resource"),
            ("reservation_date", "Reservation Date"),
            ("status", "Status"),
        ],
    ),
    "journal_sales": (
        "Journal Sales Report",
        [
            ("sale_id", "Sale ID"),
            ("journal", "Journal"),
            ("quantity", "Quantity"),
            ("sale_date", "Sale Date"),
            ("total_amount", "Total Amount"),
        ],
    ),
    "fines": (
        "Fines Report",
        [
            ("fine_id", "Fine ID"),
            ("visitor", "Visitor"),
            ("fine_type", "Fine Type"),
            ("amount", "Amount"),
            ("resource", "Resource"),
            ("date_issued", "Date Issued"),
            ("payment_status", "Payment Status"),
        ],
    ),
}


def generate_report(
    report_type: str | None,
    records: Iterable[dict[str, Any]],
    start_date: Any,
    end_date: Any,
    role: str | None,
) -> dict[str, Any]:
    """Authorize the user, validate the report type and generate the report."""
    if not role:
        raise PermissionError("Administrator login is required")
    if role.strip().lower() != "administrator":
        raise PermissionError("Only an Administrator may access reports")

    if not report_type or report_type not in REPORT_GENERATORS:
        raise ValueError("A valid report type must be selected")

    return REPORT_GENERATORS[report_type](records, start_date, end_date)


def _word_cell_value(value: Any) -> str:
    """Convert a report value to readable text for a Word table cell."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)
    return str(value)


def export_report_to_word(
    report: dict[str, Any], output_path: str | Path
) -> Path:
    """Export a generated report to a Microsoft Word ``.docx`` file."""
    report_type = report.get("report_type")
    if report_type not in REPORT_EXPORT_COLUMNS:
        raise ValueError("The report type cannot be exported to Microsoft Word")

    if "start_date" not in report or "end_date" not in report:
        raise ValueError("The report must include a start date and an end date")

    output_file = Path(output_path)
    if output_file.suffix.lower() != ".docx":
        output_file = output_file.with_suffix(".docx")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    title, columns = REPORT_EXPORT_COLUMNS[report_type]
    document = Document()
    title_style = document.styles["Title"]
    title_style.font.size = Pt(24)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    title_style_properties = title_style.element.get_or_add_pPr()
    title_border = title_style_properties.find(qn("w:pBdr"))
    if title_border is not None:
        title_style_properties.remove(title_border)

    title_paragraph = document.add_paragraph(title, style="Title")
    title_paragraph.paragraph_format.space_before = Pt(24)
    title_paragraph.paragraph_format.space_after = Pt(12)
    document.add_paragraph(
        f"Date range: {report['start_date']} to {report['end_date']}"
    )

    records = report.get("records", [])
    if not records:
        document.add_paragraph(report.get("message", NO_DATA_MESSAGE))
    else:
        table = document.add_table(rows=1, cols=len(columns))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for index, (_, heading) in enumerate(columns):
            table.rows[0].cells[index].text = heading

        for record in records:
            cells = table.add_row().cells
            for index, (field, _) in enumerate(columns):
                cells[index].text = _word_cell_value(record.get(field))

    document.save(output_file)
    return output_file
