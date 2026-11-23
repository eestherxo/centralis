"""HTTP endpoints for administrative report generation and export."""

from __future__ import annotations

from io import BytesIO
from tempfile import TemporaryDirectory
from typing import Any

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.modules.report_generation import (
    REPORT_GENERATORS,
    export_report_to_excel,
    generate_report,
    get_report_records,
)


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _role_from_token() -> str | None:
    role = get_jwt().get("role")
    if role:
        return str(role)

    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("role"):
        return str(identity["role"])

    from app.modules.authentication import get_user

    user = get_user(identity)
    if user and user.get("role"):
        return str(user["role"])
    return None


def _administrator_access_error():
    role = _role_from_token()
    if not role or role.strip().lower() not in {"admin", "administrator"}:
        return jsonify(
            {"error": "Only an Administrator may access reports"}
        ), 403
    return None


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
        raise ValueError("Report type, start date and end date are required")
    if report_type not in REPORT_GENERATORS:
        raise ValueError("A valid report type must be selected")

    return generate_report(
        report_type,
        get_report_records(report_type),
        start_date,
        end_date,
        "Administrator",
    )


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

    with TemporaryDirectory() as directory:
        report_name = f"{report['report_type']}_report.xlsx"
        report_path = export_report_to_excel(
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
            "spreadsheetml.sheet"
        ),
    )
