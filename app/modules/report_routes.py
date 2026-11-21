"""Flask routes for SALISES administrative reports.

This module is a standalone integration proposal.  The application must
provide a callable named REPORT_RECORD_PROVIDER in its Flask configuration.
The callable receives a report type and returns the stored records required
to generate that report.
"""

from __future__ import annotations

from io import BytesIO
from tempfile import TemporaryDirectory
from typing import Any, Callable

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
)
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from .reports import REPORT_GENERATORS, export_report_to_word, generate_report


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports",
    template_folder="../templates",
)

REPORT_OPTIONS = [
    ("visitor", "Visitor Report"),
    ("reservation", "Reservation Report"),
    ("journal_sales", "Journal Sales Report"),
    ("fines", "Fines Report"),
]


def _role_from_token() -> str | None:
    """Read the role claim used to authorize administrative reporting."""
    role = get_jwt().get("role")
    if role:
        return str(role)

    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("role"):
        return str(identity["role"])
    return None


def _administrator_access_error():
    role = _role_from_token()
    if not role or role.strip().lower() != "administrator":
        return jsonify(
            {"error": "Only an Administrator may access reports"}
        ), 403
    return None


def _record_provider() -> Callable[[str], list[dict[str, Any]]]:
    provider = current_app.config.get("REPORT_RECORD_PROVIDER")
    if not callable(provider):
        raise RuntimeError("The report record provider has not been configured")
    return provider


def _request_values() -> tuple[str | None, str | None, str | None]:
    payload = request.get_json(silent=True) or {}
    return (
        payload.get("report_type"),
        payload.get("start_date"),
        payload.get("end_date"),
    )


def _build_requested_report() -> dict[str, Any]:
    report_type, start_date, end_date = _request_values()

    if not report_type or not start_date or not end_date:
        raise ValueError(
            "Report type, start date and end date are required"
        )
    if report_type not in REPORT_GENERATORS:
        raise ValueError("A valid report type must be selected")

    records = _record_provider()(report_type) or []
    return generate_report(
        report_type,
        records,
        start_date,
        end_date,
        "Administrator",
    )


@reports_bp.get("/")
@jwt_required()
def reports_page():
    access_error = _administrator_access_error()
    if access_error:
        return access_error
    return render_template("reports.html", report_options=REPORT_OPTIONS)


@reports_bp.post("/generate")
@jwt_required()
def generate_report_route():
    access_error = _administrator_access_error()
    if access_error:
        return access_error

    try:
        return jsonify(_build_requested_report()), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503


@reports_bp.post("/export")
@jwt_required()
def export_report_route():
    access_error = _administrator_access_error()
    if access_error:
        return access_error

    try:
        report = _build_requested_report()
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503

    with TemporaryDirectory() as directory:
        report_name = f"{report['report_type']}_report.docx"
        report_path = export_report_to_word(
            report, f"{directory}/{report_name}"
        )
        report_bytes = BytesIO(report_path.read_bytes())

    report_bytes.seek(0)
    return send_file(
        report_bytes,
        as_attachment=True,
        download_name=report_name,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )
