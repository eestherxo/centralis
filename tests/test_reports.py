"""Automated functional tests for SALISES User Story 03."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import load_workbook

try:
    from app.modules.report_generation import (
        NO_DATA_MESSAGE,
        export_report_to_excel,
        generate_report,
    )
except ModuleNotFoundError:
    from report_generation import (
        NO_DATA_MESSAGE,
        export_report_to_excel,
        generate_report,
    )


ADMIN = "Administrator"
START_DATE = "2026-11-01"
END_DATE = "2026-11-30"


class ReportTests(unittest.TestCase):
    # TC-3.01: Visitor report generated successfully.
    def test_01_visitor_report(self):
        visits = [
            {
                "visitor_id": "V-001",
                "name": "Maya Brown",
                "type": "Undergraduate",
                "check_in": "2026-11-02",
            },
            {
                "visitor_id": "V-001",
                "name": "Maya Brown",
                "type": "Undergraduate",
                "check_in": "2026-11-08",
            },
        ]

        report = generate_report(
            "visitor", visits, START_DATE, END_DATE, ADMIN
        )

        self.assertEqual(report["report_type"], "visitor")
        self.assertEqual(report["records"][0]["name"], "Maya Brown")
        self.assertEqual(report["records"][0]["visit_frequency"], 2)
        self.assertEqual(
            report["records"][0]["visit_dates"],
            ["2026-11-02", "2026-11-08"],
        )

    # TC-3.02: Reservation report generated successfully.
    def test_02_reservation_report(self):
        reservations = [
            {
                "id": "RS-001",
                "visitor_id": "Maya Brown",
                "resource_id": "Seminar Room 1",
                "request_date": "2026-11-10",
                "status": "Approved",
            }
        ]

        report = generate_report(
            "reservation", reservations, START_DATE, END_DATE, ADMIN
        )

        self.assertEqual(report["records"][0]["resource_id"], "Seminar Room 1")
        self.assertEqual(report["records"][0]["status"], "Approved")

    # TC-3.03: Journal-sales report generated successfully.
    def test_03_journal_sales_report(self):
        sales = [
            {
                "id": "S-001",
                "journal_id": "Social and Economic Studies",
                "quantity": 2,
                "date_sold": "2026-11-12",
                "sale_amount": 5000.00,
            }
        ]

        report = generate_report(
            "journal_sales", sales, START_DATE, END_DATE, ADMIN
        )

        self.assertEqual(report["records"][0]["quantity"], 2)
        self.assertEqual(report["records"][0]["sale_amount"], 5000.00)

    # TC-3.04: Fine report generated successfully.
    def test_04_fines_report(self):
        fines = [
            {
                "id": "F-001",
                "visitor_id": "Maya Brown",
                "reason": "Overdue",
                "amount": 150.00,
                "resource_id": "Caribbean Development",
                "date_issued": "2026-11-15",
                "status": "Unpaid",
            }
        ]

        report = generate_report("fines", fines, START_DATE, END_DATE, ADMIN)

        self.assertEqual(report["records"][0]["reason"], "Overdue")
        self.assertEqual(report["records"][0]["amount"], 150.00)

    # TC-3.05: A non-Administrator is denied access.
    def test_05_non_administrator_denied(self):
        with self.assertRaisesRegex(PermissionError, "Only an Administrator"):
            generate_report("visitor", [], START_DATE, END_DATE, "Staff")

    # TC-3.06: An invalid date range is rejected.
    def test_06_invalid_date_range(self):
        with self.assertRaisesRegex(ValueError, "start date"):
            generate_report(
                "visitor", [], "2026-11-30", "2026-11-01", ADMIN
            )

    # TC-3.07: No matching records produces the required message.
    def test_07_no_data_available(self):
        visits = [
            {
                "visitor_id": "V-001",
                "name": "Maya Brown",
                "type": "Undergraduate",
                "check_in": "2026-10-15",
            }
        ]

        report = generate_report(
            "visitor", visits, START_DATE, END_DATE, ADMIN
        )

        self.assertEqual(report["records"], [])
        self.assertEqual(report["message"], NO_DATA_MESSAGE)

    # TC-3.08: A report cannot be generated without a report type.
    def test_08_report_type_required(self):
        with self.assertRaisesRegex(ValueError, "report type"):
            generate_report(None, [], START_DATE, END_DATE, ADMIN)

    # TC-3.09: A logged-out user cannot directly access reporting.
    def test_09_logged_out_user_denied(self):
        with self.assertRaisesRegex(PermissionError, "login is required"):
            generate_report("visitor", [], START_DATE, END_DATE, None)

    # TC-3.10: Report values match storage and stored records are unchanged.
    def test_10_stored_records_are_not_changed(self):
        reservations = [
            {
                "id": "RS-002",
                "visitor_id": "Daniel King",
                "resource_id": "Meeting Room 2",
                "request_date": "2026-11-11",
                "status": "Pending",
            }
        ]
        original = deepcopy(reservations)

        report = generate_report(
            "reservation", reservations, START_DATE, END_DATE, ADMIN
        )

        self.assertEqual(reservations, original)
        self.assertEqual(report["records"][0]["id"], "RS-002")
        self.assertEqual(report["records"][0]["status"], "Pending")

    # TC-3.11: A single-day visitor range includes that day's visits.
    def test_11_single_day_visitor_report(self):
        visits = [
            {
                "visitor_id": "V-002",
                "name": "Daniel King",
                "type": "Postgraduate",
                "check_in": "2026-11-14",
            },
            {
                "visitor_id": "V-002",
                "name": "Daniel King",
                "type": "Postgraduate",
                "check_in": "2026-11-15",
            },
        ]

        report = generate_report(
            "visitor", visits, "2026-11-14", "2026-11-14", ADMIN
        )

        self.assertEqual(report["records"][0]["visit_dates"], ["2026-11-14"])
        self.assertEqual(report["records"][0]["visit_frequency"], 1)

    # TC-3.12: Visitor categories remain distinguishable in the report.
    def test_12_visitor_categories(self):
        visits = [
            {
                "visitor_id": "V-003",
                "name": "Leah Grant",
                "type": "undergraduate",
                "check_in": "2026-11-03",
            },
            {
                "visitor_id": "V-004",
                "name": "Owen Clarke",
                "type": "external",
                "check_in": "2026-11-04",
            },
        ]

        report = generate_report(
            "visitor", visits, START_DATE, END_DATE, ADMIN
        )

        categories = {
            record["name"]: record["type"]
            for record in report["records"]
        }
        self.assertEqual(
            categories,
            {
                "Leah Grant": "undergraduate",
                "Owen Clarke": "external",
            },
        )
        self.assertTrue(
            all(record["visit_frequency"] == 1 for record in report["records"])
        )

    # TC-3.13: Reservation statuses are reported separately.
    def test_13_reservation_statuses(self):
        reservations = [
            {
                "id": "RS-003",
                "visitor_id": "Maya Brown",
                "resource_id": "Seminar Room 1",
                "request_date": "2026-11-10",
                "status": "declined",
            },
            {
                "id": "RS-004",
                "visitor_id": "Daniel King",
                "resource_id": "Meeting Room 2",
                "request_date": "2026-11-11",
                "status": "cancelled",
            },
        ]

        report = generate_report(
            "reservation", reservations, START_DATE, END_DATE, ADMIN
        )

        statuses = {
            record["id"]: record["status"]
            for record in report["records"]
        }
        self.assertEqual(
            statuses,
            {
                "RS-003": "declined",
                "RS-004": "cancelled",
            },
        )

    # TC-3.14: Different reserved resource types are shown.
    def test_14_different_reserved_resources(self):
        reservations = [
            {
                "id": "RS-005",
                "visitor_id": "Maya Brown",
                "resource_id": "Seminar Room 1",
                "request_date": "2026-11-13",
                "status": "approved",
            },
            {
                "id": "RS-006",
                "visitor_id": "Daniel King",
                "resource_id": "Archival A-003",
                "request_date": "2026-11-14",
                "status": "pending",
            },
            {
                "id": "RS-007",
                "visitor_id": "Leah Grant",
                "resource_id": "Book B-020",
                "request_date": "2026-11-15",
                "status": "cancelled",
            },
        ]

        report = generate_report(
            "reservation",
            reservations,
            "2026-11-13",
            "2026-11-15",
            ADMIN,
        )

        reported = {
            record["id"]: (
                record["resource_id"],
                record["request_date"],
                record["status"],
            )
            for record in report["records"]
        }
        self.assertEqual(
            reported,
            {
                "RS-005": ("Seminar Room 1", "2026-11-13", "approved"),
                "RS-006": ("Archival A-003", "2026-11-14", "pending"),
                "RS-007": ("Book B-020", "2026-11-15", "cancelled"),
            },
        )

    # TC-3.15: Multiple sales of the same journal are all included.
    def test_15_multiple_sales_same_journal(self):
        sales = [
            {
                "id": "SALE-002",
                "journal_id": "J-001",
                "quantity": 1,
                "date_sold": "2026-11-13",
                "sale_amount": 1500.00,
            },
            {
                "id": "SALE-003",
                "journal_id": "J-001",
                "quantity": 3,
                "date_sold": "2026-11-14",
                "sale_amount": 4500.00,
            },
        ]

        report = generate_report(
            "journal_sales",
            sales,
            "2026-11-13",
            "2026-11-14",
            ADMIN,
        )

        reported = {
            record["id"]: (
                record["journal_id"],
                record["quantity"],
                record["date_sold"],
                record["sale_amount"],
            )
            for record in report["records"]
        }

        self.assertEqual(
            reported,
            {
                "SALE-002": ("J-001", 1, "2026-11-13", 1500.00),
                "SALE-003": ("J-001", 3, "2026-11-14", 4500.00),
            },
        )

    # TC-3.16: Different journals sold on the same date remain separate.
    def test_16_different_journals_same_date(self):
        sales = [
            {
                "id": "SALE-004",
                "journal_id": "J-002",
                "quantity": 2,
                "date_sold": "2026-11-15",
                "sale_amount": 2500.00,
            },
            {
                "id": "SALE-005",
                "journal_id": "J-003",
                "quantity": 1,
                "date_sold": "2026-11-15",
                "sale_amount": 2000.00,
            },
        ]

        report = generate_report(
            "journal_sales",
            sales,
            "2026-11-15",
            "2026-11-15",
            ADMIN,
        )

        reported = {
            record["id"]: (
                record["journal_id"],
                record["quantity"],
                record["date_sold"],
                record["sale_amount"],
            )
            for record in report["records"]
        }

        self.assertEqual(
            reported,
            {
                "SALE-004": ("J-002", 2, "2026-11-15", 2500.00),
                "SALE-005": ("J-003", 1, "2026-11-15", 2000.00),
            },
        )

    # TC-3.17: Different fine types remain distinguishable.
    def test_17_fine_reasons(self):
        fines = [
            {
                "id": "FINE-002",
                "visitor_id": "V-004",
                "reason": "late",
                "amount": 100.00,
                "resource_id": "B-020",
                "date_issued": "2026-11-16",
                "status": "unpaid",
            },
            {
                "id": "FINE-003",
                "visitor_id": "V-005",
                "reason": "lost",
                "amount": 2500.00,
                "resource_id": "B-021",
                "date_issued": "2026-11-17",
                "status": "unpaid",
            },
            {
                "id": "FINE-004",
                "visitor_id": "V-006",
                "reason": "damaged",
                "amount": 1200.00,
                "resource_id": "J-005",
                "date_issued": "2026-11-18",
                "status": "unpaid",
            },
        ]

        report = generate_report(
            "fines",
            fines,
            "2026-11-16",
            "2026-11-18",
            ADMIN,
        )

        reported = {
            record["id"]: (
                record["visitor_id"],
                record["reason"],
                record["amount"],
                record["resource_id"],
                record["date_issued"],
                record["status"],
            )
            for record in report["records"]
        }

        self.assertEqual(
            reported,
            {
                "FINE-002": (
                    "V-004",
                    "late",
                    100.00,
                    "B-020",
                    "2026-11-16",
                    "unpaid",
                ),
                "FINE-003": (
                    "V-005",
                    "lost",
                    2500.00,
                    "B-021",
                    "2026-11-17",
                    "unpaid",
                ),
                "FINE-004": (
                    "V-006",
                    "damaged",
                    1200.00,
                    "J-005",
                    "2026-11-18",
                    "unpaid",
                ),
            },
        )

    # TC-3.18: Paid and unpaid fines are both reported accurately.
    def test_18_fine_payment_statuses(self):
        fines = [
            {
                "id": "FINE-005",
                "visitor_id": "V-007",
                "reason": "late",
                "amount": 50.00,
                "resource_id": "B-022",
                "date_issued": "2026-11-19",
                "status": "paid",
            },
            {
                "id": "FINE-006",
                "visitor_id": "V-008",
                "reason": "damaged",
                "amount": 200.00,
                "resource_id": "B-023",
                "date_issued": "2026-11-20",
                "status": "unpaid",
            },
        ]

        report = generate_report(
            "fines",
            fines,
            "2026-11-19",
            "2026-11-20",
            ADMIN,
        )

        reported = {
            record["id"]: (
                record["visitor_id"],
                record["reason"],
                record["amount"],
                record["resource_id"],
                record["date_issued"],
                record["status"],
            )
            for record in report["records"]
        }

        self.assertEqual(
            reported,
            {
                "FINE-005": (
                    "V-007",
                    "late",
                    50.00,
                    "B-022",
                    "2026-11-19",
                    "paid",
                ),
                "FINE-006": (
                    "V-008",
                    "damaged",
                    200.00,
                    "B-023",
                    "2026-11-20",
                    "unpaid",
                ),
            },
        )

    # TC-3.19: A generated report can be exported to Microsoft Excel.
    def test_19_export_report_to_excel(self):
        visits = [
            {
                "visitor_id": "V-001",
                "name": "Maya Brown",
                "type": "undergraduate",
                "check_in": "2026-11-02",
            },
            {
                "visitor_id": "V-002",
                "name": "Omar Lewis",
                "type": "external",
                "check_in": "2026-11-03",
            },
        ]

        report = generate_report(
            "visitor",
            visits,
            "2026-11-01",
            "2026-11-07",
            ADMIN,
        )

        with TemporaryDirectory() as directory:
            requested_path = Path(directory) / "visitor_report.xlsx"
            exported_path = export_report_to_excel(report, requested_path)

            self.assertTrue(exported_path.exists())
            self.assertEqual(exported_path.suffix, ".xlsx")

            workbook = load_workbook(exported_path)
            worksheet = workbook.active

            self.assertEqual(worksheet.title, "Visitor Report")
            self.assertEqual(worksheet["A1"].value, "Visitor Report")
            self.assertEqual(
                worksheet["A2"].value,
                "Date range: 2026-11-01 to 2026-11-07",
            )

            headings = [cell.value for cell in worksheet[4]]
            self.assertEqual(
                headings,
                [
                    "Visitor ID",
                    "Visitor Name",
                    "Visitor Type",
                    "Visit Dates",
                    "Visit Frequency",
                ],
            )

            exported_rows = [
                list(row)
                for row in worksheet.iter_rows(
                    min_row=5,
                    values_only=True,
                )
            ]
            self.assertEqual(
                exported_rows,
                [
                    [
                        "V-001",
                        "Maya Brown",
                        "undergraduate",
                        "2026-11-02",
                        1,
                    ],
                    [
                        "V-002",
                        "Omar Lewis",
                        "external",
                        "2026-11-03",
                        1,
                    ],
                ],
            )

            workbook.close()


if __name__ == "__main__":
    unittest.main()
