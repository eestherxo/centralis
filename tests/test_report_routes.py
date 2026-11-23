"""Integration tests for the administrative reporting endpoints."""

from io import BytesIO
import unittest
from unittest.mock import patch

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from openpyxl import load_workbook

from app.routes.reports import reports_bp


class ReportRouteTests(unittest.TestCase):
    def setUp(self):
        self.records = {
            "visitor": [
                {
                    "visitor_id": "V-001",
                    "name": "Maya Brown",
                    "type": "undergraduate",
                    "check_in": "2026-11-02T09:30:00+00:00",
                }
            ],
            "reservation": [],
            "journal_sales": [],
            "fines": [],
        }

        self.record_patch = patch(
            "app.routes.reports.get_report_records",
            side_effect=lambda report_type: self.records[report_type],
        )
        self.record_patch.start()
        self.addCleanup(self.record_patch.stop)

        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="report-route-test-secret-at-least-32-bytes",
        )
        JWTManager(self.app)
        self.app.register_blueprint(reports_bp)
        self.client = self.app.test_client()

        with self.app.app_context():
            self.admin_token = create_access_token(
                identity="admin-001",
                additional_claims={"role": "Administrator"},
            )
            self.staff_token = create_access_token(
                identity="staff-001",
                additional_claims={"role": "Staff"},
            )

    @staticmethod
    def _headers(token):
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _visitor_request():
        return {
            "report_type": "visitor",
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
        }

    def test_administrator_can_generate_visitor_report(self):
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.admin_token),
            json=self._visitor_request(),
        )
        self.assertEqual(response.status_code, 200)
        report = response.get_json()
        self.assertEqual(report["report_type"], "visitor")
        self.assertEqual(report["records"][0]["name"], "Maya Brown")

    def test_non_administrator_is_denied(self):
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.staff_token),
            json=self._visitor_request(),
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only an Administrator", response.get_json()["error"])

    def test_logged_out_user_is_denied(self):
        response = self.client.post(
            "/reports/generate", json=self._visitor_request()
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_date_range_is_rejected(self):
        request_data = self._visitor_request()
        request_data["start_date"] = "2026-11-10"
        request_data["end_date"] = "2026-11-01"
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.admin_token),
            json=request_data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("start date", response.get_json()["error"])

    def test_report_type_is_required(self):
        request_data = self._visitor_request()
        request_data["report_type"] = ""
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.admin_token),
            json=request_data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("required", response.get_json()["error"])

    def test_invalid_report_type_is_rejected(self):
        request_data = self._visitor_request()
        request_data["report_type"] = "unknown"
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.admin_token),
            json=request_data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid report type", response.get_json()["error"])

    def test_no_data_message_is_returned(self):
        request_data = self._visitor_request()
        request_data["report_type"] = "fines"
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.admin_token),
            json=request_data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], "No data available")

    def test_administrator_can_export_excel_report(self):
        response = self.client.post(
            "/reports/export",
            headers=self._headers(self.admin_token),
            json=self._visitor_request(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml.sheet", response.content_type)
        self.assertIn(
            "visitor_report.xlsx", response.headers["Content-Disposition"]
        )

        worksheet = load_workbook(BytesIO(response.data)).active
        self.assertEqual(worksheet["A1"].value, "Visitor Report")
        self.assertEqual(worksheet["B5"].value, "Maya Brown")


if __name__ == "__main__":
    unittest.main()
