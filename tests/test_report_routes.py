"""Integration tests for the proposed administrative reporting routes."""

from io import BytesIO
import unittest

from openpyxl import load_workbook
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app.modules.report_routes import reports_bp


class ReportRouteTests(unittest.TestCase):
    def setUp(self):
        self.records = {
            "visitor": [
                {
                    "visitor_id": "V-001",
                    "visitor_name": "Maya Brown",
                    "visitor_type": "Undergraduate",
                    "visit_date": "2026-11-02",
                }
            ],
            "reservation": [],
            "journal_sales": [],
            "fines": [],
        }

        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="report-route-test-secret-at-least-32-bytes",
            REPORT_RECORD_PROVIDER=lambda report_type: self.records[report_type],
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

    def _headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def _visitor_request(self):
        return {
            "report_type": "visitor",
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
        }

    def test_administrator_can_open_reports_page(self):
        response = self.client.get(
            "/reports/", headers=self._headers(self.admin_token)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Administrative Reports", response.data)

    def test_administrator_can_generate_visitor_report(self):
        response = self.client.post(
            "/reports/generate",
            headers=self._headers(self.admin_token),
            json=self._visitor_request(),
        )
        self.assertEqual(response.status_code, 200)
        report = response.get_json()
        self.assertEqual(report["report_type"], "visitor")
        self.assertEqual(report["records"][0]["visitor_name"], "Maya Brown")

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
        self.assertIn(
            "application/vnd.openxmlformats-officedocument",
            response.content_type,
        )
        self.assertIn("spreadsheetml.sheet", response.content_type)
        self.assertIn("visitor_report.xlsx", response.headers["Content-Disposition"])

        worksheet = load_workbook(BytesIO(response.data)).active
        self.assertEqual(worksheet["A1"].value, "Visitor Report")
        self.assertEqual(
            worksheet["B5"].value,
            "Maya Brown",
        )


if __name__ == "__main__":
    unittest.main()
