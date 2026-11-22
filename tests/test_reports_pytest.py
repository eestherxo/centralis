"""Pytest verification of the report generation business logic."""

from copy import deepcopy
from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.modules.report_generation import (
    NO_DATA_MESSAGE,
    export_report_to_excel,
    generate_report,
)
from tests.mock_data import MOCK_REPORT_DATA


ADMIN = "Administrator"
START_DATE = "2026-11-01"
END_DATE = "2026-11-30"


@pytest.fixture
def mock_records():
    """Give each test an independent copy of the provisional records."""
    return deepcopy(MOCK_REPORT_DATA)


@pytest.mark.parametrize(
    ("report_type", "expected_records"),
    [
        ("visitor", 3),
        ("reservation", 2),
        ("journal_sales", 2),
        ("fines", 2),
    ],
)
def test_each_supported_report_type(mock_records, report_type, expected_records):
    report = generate_report(
        report_type,
        mock_records[report_type],
        START_DATE,
        END_DATE,
        ADMIN,
    )

    assert report["report_type"] == report_type
    assert len(report["records"]) == expected_records


def test_date_range_includes_boundary_dates_and_excludes_outside_records(
    mock_records,
):
    report = generate_report(
        "visitor", mock_records["visitor"], START_DATE, END_DATE, ADMIN
    )

    included_dates = {
        visit_date
        for visitor in report["records"]
        for visit_date in visitor["visit_dates"]
    }
    assert "2026-11-01" in included_dates
    assert "2026-11-30" in included_dates
    assert "2026-12-01" not in included_dates


def test_visitor_frequency_and_categories_are_reported(mock_records):
    report = generate_report(
        "visitor", mock_records["visitor"], START_DATE, END_DATE, ADMIN
    )

    maya = next(
        record for record in report["records"] if record["visitor_id"] == "V-001"
    )
    categories = {record["type"] for record in report["records"]}

    assert maya["visit_frequency"] == 2
    assert categories == {
        "Undergraduate",
        "Postgraduate",
        "Outside Personnel",
    }


def test_no_matching_records_returns_required_message(mock_records):
    report = generate_report(
        "fines",
        mock_records["fines"],
        "2027-01-01",
        "2027-01-31",
        ADMIN,
    )

    assert report["records"] == []
    assert report["message"] == NO_DATA_MESSAGE


@pytest.mark.parametrize("role", [None, "Staff"])
def test_unauthorized_roles_cannot_generate_reports(mock_records, role):
    with pytest.raises(PermissionError):
        generate_report(
            "visitor",
            mock_records["visitor"],
            START_DATE,
            END_DATE,
            role,
        )


def test_invalid_date_range_is_rejected(mock_records):
    with pytest.raises(ValueError, match="start date"):
        generate_report(
            "visitor",
            mock_records["visitor"],
            END_DATE,
            START_DATE,
            ADMIN,
        )


def test_missing_required_record_field_is_reported(mock_records):
    del mock_records["reservation"][0]["status"]

    with pytest.raises(ValueError, match="Missing required field: status"):
        generate_report(
            "reservation",
            mock_records["reservation"],
            START_DATE,
            END_DATE,
            ADMIN,
        )


@pytest.mark.parametrize(
    "report_type",
    ["visitor", "reservation", "journal_sales", "fines"],
)
def test_each_supported_report_can_be_exported_to_excel(
    mock_records, report_type, tmp_path: Path
):
    report = generate_report(
        report_type,
        mock_records[report_type],
        START_DATE,
        END_DATE,
        ADMIN,
    )
    output_file = export_report_to_excel(
        report, tmp_path / f"{report_type}_report.xlsx"
    )

    worksheet = load_workbook(output_file).active
    assert output_file.exists()
    assert output_file.suffix == ".xlsx"
    assert worksheet["A1"].value.endswith("Report")
    assert worksheet.max_row == len(report["records"]) + 4
