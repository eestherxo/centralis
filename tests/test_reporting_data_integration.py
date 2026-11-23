"""Integration tests using the real reporting data-access pipeline."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app import data_access
from app.routes.reports import reports_bp


class ReportingDataIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)

        self.db_patch = patch.object(
            data_access,
            "DB_DIR",
            Path(self.temp_directory.name),
        )
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)

        self.visitor = data_access.create(
            "visitor",
            {
                "name": "Integration Visitor",
                "type": "Student",
            },
        )

        data_access.create(
            "visit",
            {
                "visitor_id": self.visitor["id"],
                "purpose": "Research",
                "check_in": "2026-11-15T09:30:00+00:00",
                "check_out": "2026-11-15T11:00:00+00:00",
            },
        )

        self.reservation = data_access.create(
            "reservation",
            {
                "visitor_id": self.visitor["id"],
                "resource_id": 29200001,
                "request_date": "2026-11-16",
                "status": "approved",
            },
        )

        self.sale = data_access.create(
            "sale",
            {
                "journal_id": 49400001,
                "quantity": 2,
                "date_sold": "2026-11-17",
                "sale_amount": 500,
            },
        )

        self.fine = data_access.create(
            "fine",
            {
                "visitor_id": self.visitor["id"],
                "reason": "Late return",
                "amount": 50,
                "resource_id": 29200001,
                "date_issued": "2026-11-18",
                "status": "unpaid",
            },
        )

        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="report-integration-secret-at-least-32-bytes",
        )
        JWTManager(self.app)
        self.app.register_blueprint(reports_bp)
        self.client = self.app.test_client()

        with self.app.app_context():
            self.admin_token = create_access_token(
                identity="admin-001",
                additional_claims={"role": "Administrator"},
            )

    def _generate_report(self, report_type):
        response = self.client.post(
            "/reports/generate",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "report_type": report_type,
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.get_data(as_text=True),
        )
        return response.get_json()

    def test_visitor_report_reads_real_visit_data(self):
        report = self._generate_report("visitor")
        record = report["records"][0]

        self.assertEqual(record["visitor_id"], self.visitor["id"])
        self.assertEqual(record["name"], "Integration Visitor")
        self.assertEqual(record["type"], "Student")
        self.assertEqual(record["visit_dates"], ["2026-11-15"])
        self.assertEqual(record["visit_frequency"], 1)

    def test_reservation_report_reads_real_reservation_data(self):
        report = self._generate_report("reservation")
        record = report["records"][0]

        self.assertEqual(record["id"], self.reservation["id"])
        self.assertEqual(record["visitor_id"], self.visitor["id"])
        self.assertEqual(record["request_date"], "2026-11-16")
        self.assertEqual(record["status"], "approved")

    def test_journal_sales_report_reads_real_sale_data(self):
        report = self._generate_report("journal_sales")
        record = report["records"][0]

        self.assertEqual(record["id"], self.sale["id"])
        self.assertEqual(record["journal_id"], 49400001)
        self.assertEqual(record["quantity"], 2)
        self.assertEqual(record["sale_amount"], 500)

    def test_fines_report_reads_real_fine_data(self):
        report = self._generate_report("fines")
        record = report["records"][0]

        self.assertEqual(record["id"], self.fine["id"])
        self.assertEqual(record["visitor_id"], self.visitor["id"])
        self.assertEqual(record["reason"], "Late return")
        self.assertEqual(record["amount"], 50)
        self.assertEqual(record["status"], "unpaid")


if __name__ == "__main__":
    unittest.main()