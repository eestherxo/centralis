"""Automated functional tests for SALISES User Story 03."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from pprint import pprint

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

def show_test_result(test_id, expected, actual):
    print(f"\n{test_id} — EXPECTED RESULT")
    pprint(expected, sort_dicts=False)

    print(f"\n{test_id} — ACTUAL RESULT")
    pprint(actual, sort_dicts=False)

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
        expected_report = {
            "report_type": "visitor",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
                {
                    "visitor_id": "V-001",
                    "name": "Maya Brown",
                    "type": "Undergraduate",
                    "visit_dates": ["2026-11-02", "2026-11-08"],
                    "visit_frequency": 2,
                }
            ],
        }

        print("\nTC-3.01 — EXPECTED RESULT")
        pprint(expected_report)

        print("\nTC-3.01 — ACTUAL RESULT")
        pprint(report)

        self.assertEqual(report, expected_report)

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

        expected_report = {
            "report_type": "reservation",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
                {
                    "id": "RS-001",
                    "visitor_id": "Maya Brown",
                    "resource_id": "Seminar Room 1",
                    "request_date": "2026-11-10",
                    "status": "Approved",
                }
            ],
        }

        show_test_result("TC-3.02", expected_report, report)

        self.assertEqual(report, expected_report)

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

        expected_report = {
            "report_type": "journal_sales",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
                {
                    "id": "S-001",
                    "journal_id": "Social and Economic Studies",
                    "quantity": 2,
                    "date_sold": "2026-11-12",
                    "sale_amount": 5000.00,
                }
            ],
        }

        show_test_result("TC-3.03", expected_report, report)

        self.assertEqual(report, expected_report)

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

        expected_report = {
            "report_type": "fines",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
                {
                    "id": "F-001",
                    "visitor_id": "Maya Brown",
                    "reason": "Overdue",
                    "amount": 150.00,
                    "resource_id": "Caribbean Development",
                    "date_issued": "2026-11-15",
                    "status": "Unpaid",
                }
            ],
        }

        show_test_result("TC-3.04", expected_report, report)

        self.assertEqual(report, expected_report)

    # TC-3.05: A non-Administrator is denied access.
    # TC-3.05: A non-Administrator is denied access.
    def test_05_non_administrator_denied(self):
        expected_result = {
            "role": "Staff",
            "access": "DENIED",
            "message": "Only an Administrator may access reports",
            "report_generated": False,
        }

        with self.assertRaisesRegex(
            PermissionError,
            "Only an Administrator",
        ) as raised:
            generate_report(
                "visitor",
                [],
                START_DATE,
                END_DATE,
                "Staff",
            )

        actual_result = {
            "role": "Staff",
            "access": "DENIED",
            "message": str(raised.exception),
            "report_generated": False,
        }

        show_test_result("TC-3.05", expected_result, actual_result)

        self.assertEqual(actual_result, expected_result)

    # TC-3.06: An invalid date range is rejected.
   # TC-3.06: An invalid date range is rejected.
    def test_06_invalid_date_range(self):
        expected_result = {
            "report_type": "visitor",
            "start_date": "2026-11-30",
            "end_date": "2026-11-01",
            "status": "REJECTED",
            "message": "The start date cannot be later than the end date",
            "report_generated": False,
        }

        with self.assertRaisesRegex(ValueError, "start date") as raised:
            generate_report(
                "visitor",
                [],
                "2026-11-30",
                "2026-11-01",
                ADMIN,
            )

        actual_result = {
            "report_type": "visitor",
            "start_date": "2026-11-30",
            "end_date": "2026-11-01",
            "status": "REJECTED",
            "message": str(raised.exception),
            "report_generated": False,
        }

        show_test_result("TC-3.06", expected_result, actual_result)

        self.assertEqual(actual_result, expected_result)

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

        expected_report = {
            "report_type": "visitor",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [],
            "message": NO_DATA_MESSAGE,
        }

        show_test_result("TC-3.07", expected_report, report)

        self.assertEqual(report, expected_report)

    # TC-3.08: A report cannot be generated without a report type.
    def test_08_report_type_required(self):
        expected_result = {
            "report_type": None,
            "status": "REJECTED",
            "message": "A valid report type must be selected",
            "report_generated": False,
        }

        with self.assertRaisesRegex(ValueError, "report type") as raised:
            generate_report(
                None,
                [],
                START_DATE,
                END_DATE,
                ADMIN,
            )

        actual_result = {
            "report_type": None,
            "status": "REJECTED",
            "message": str(raised.exception),
            "report_generated": False,
        }

        show_test_result("TC-3.08", expected_result, actual_result)

        self.assertEqual(actual_result, expected_result)

    # TC-3.09: A logged-out user cannot directly access reporting.
    # TC-3.09: A logged-out user cannot directly access reporting.
    def test_09_logged_out_user_denied(self):
        expected_result = {
            "role": None,
            "user_state": "Logged out",
            "access": "DENIED",
            "message": "Administrator login is required",
            "report_generated": False,
        }

        with self.assertRaisesRegex(
            PermissionError,
            "login is required",
        ) as raised:
            generate_report(
                "visitor",
                [],
                START_DATE,
                END_DATE,
                None,
            )

        actual_result = {
            "role": None,
            "user_state": "Logged out",
            "access": "DENIED",
            "message": str(raised.exception),
            "report_generated": False,
        }

        show_test_result("TC-3.09", expected_result, actual_result)

        self.assertEqual(actual_result, expected_result)

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

        expected_report = {
            "report_type": "reservation",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
                {
                    "id": "RS-002",
                    "visitor_id": "Daniel King",
                    "resource_id": "Meeting Room 2",
                    "request_date": "2026-11-11",
                    "status": "Pending",
                }
            ],
        }

        expected_result = {
            "original_input": original,
            "generated_report": expected_report,
            "input_after_generation": original,
            "input_unchanged": True,
        }

        actual_result = {
            "original_input": original,
            "generated_report": report,
            "input_after_generation": reservations,
            "input_unchanged": reservations == original,
        }

        show_test_result("TC-3.10", expected_result, actual_result)

        self.assertEqual(actual_result, expected_result)

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

        expected_report = {
            "report_type": "visitor",
            "start_date": "2026-11-14",
            "end_date": "2026-11-14",
            "records": [
                {
                    "visitor_id": "V-002",
                    "name": "Daniel King",
                    "type": "Postgraduate",
                    "visit_dates": ["2026-11-14"],
                    "visit_frequency": 1,
                }
            ],
        }

        show_test_result("TC-3.11", expected_report, report)

        self.assertEqual(report, expected_report)

    # TC-3.12: Visitor categories remain distinguishable in the report.
    # TC-3.12: Visitor categories remain distinguishable in the report.
    def test_12_visitor_categories(self):
        visits = [
            {
                "visitor_id": "V-003",
                "name": "Leah Grant",
                "type": "Undergraduate",
                "check_in": "2026-11-03",
            },
            {
                "visitor_id": "V-004",
                "name": "Owen Clarke",
                "type": "External",
                "check_in": "2026-11-04",
            },
        ]

        report = generate_report(
            "visitor", visits, START_DATE, END_DATE, ADMIN
        )

        expected_report = {
            "report_type": "visitor",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
                {
                    "visitor_id": "V-003",
                    "name": "Leah Grant",
                    "type": "Undergraduate",
                    "visit_dates": ["2026-11-03"],
                    "visit_frequency": 1,
                },
                {
                    "visitor_id": "V-004",
                    "name": "Owen Clarke",
                    "type": "External",
                    "visit_dates": ["2026-11-04"],
                    "visit_frequency": 1,
                },
            ],
        }

        show_test_result("TC-3.12", expected_report, report)

        self.assertEqual(report, expected_report)

    # TC-3.13: Reservation statuses are reported separately.
    # TC-3.13: Supported reservation statuses remain associated
    # with the correct reservations.
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

        expected_report = {
            "report_type": "reservation",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "records": [
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
            ],
        }

        show_test_result("TC-3.13", expected_report, report)
        self.assertEqual(report, expected_report)

    # TC-3.14: Different reserved resource types are shown.
    # TC-3.14: Different reserved resources are displayed correctly.
    def test_14_reservation_resource_types(self):
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

        expected_report = {
            "report_type": "reservation",
            "start_date": "2026-11-13",
            "end_date": "2026-11-15",
            "records": [
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
            ],
        }

        show_test_result("TC-3.14", expected_report, report)
        self.assertEqual(report, expected_report)

    # TC-3.15: Multiple sales of the same journal are all included.
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

        expected_report = {
            "report_type": "journal_sales",
            "start_date": "2026-11-13",
            "end_date": "2026-11-14",
            "records": [
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
            ],
        }

        show_test_result("TC-3.15", expected_report, report)
        self.assertEqual(report, expected_report)

    # TC-3.16: Different journals sold on the same date remain separate.
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

        expected_report = {
            "report_type": "journal_sales",
            "start_date": "2026-11-15",
            "end_date": "2026-11-15",
            "records": [
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
            ],
        }

        show_test_result("TC-3.16", expected_report, report)
        self.assertEqual(report, expected_report)

    # TC-3.17: Different fine types remain distinguishable.
    # TC-3.17: Different fine reasons remain associated
    # with the correct fine records.
    def test_17_fine_types(self):
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

        expected_report = {
            "report_type": "fines",
            "start_date": "2026-11-16",
            "end_date": "2026-11-18",
            "records": [
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
            ],
        }

        show_test_result("TC-3.17", expected_report, report)
        self.assertEqual(report, expected_report)

    # TC-3.18: Paid and unpaid fines are reported
    # with their correct payment statuses.
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

        expected_report = {
            "report_type": "fines",
            "start_date": "2026-11-19",
            "end_date": "2026-11-20",
            "records": [
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
            ],
        }

        show_test_result("TC-3.18", expected_report, report)
        self.assertEqual(report, expected_report)

    # TC-3.19: A generated report can be exported to Microsoft Excel.
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

        expected_export = {
            "file_created": True,
            "file_extension": ".xlsx",
            "worksheet_name": "Visitor Report",
            "report_title": "Visitor Report",
            "date_range": "Date range: 2026-11-01 to 2026-11-07",
            "headings": [
                "Visitor ID",
                "Visitor Name",
                "Visitor Type",
                "Visit Dates",
                "Visit Frequency",
            ],
            "rows": [
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
        }

        with TemporaryDirectory() as directory:
            requested_path = Path(directory) / "visitor_report.xlsx"
            exported_path = export_report_to_excel(report, requested_path)

            workbook = load_workbook(exported_path)
            worksheet = workbook.active

            exported_rows = [
                list(row)
                for row in worksheet.iter_rows(
                    min_row=5,
                    values_only=True,
                )
            ]

            actual_export = {
                "file_created": exported_path.exists(),
                "file_extension": exported_path.suffix,
                "worksheet_name": worksheet.title,
                "report_title": worksheet["A1"].value,
                "date_range": worksheet["A2"].value,
                "headings": [
                    cell.value for cell in worksheet[4]
                ],
                "rows": exported_rows,
            }

            show_test_result(
                "TC-3.19",
                expected_export,
                actual_export,
            )
            self.assertEqual(actual_export, expected_export)

            workbook.close()


if __name__ == "__main__":
    unittest.main()
