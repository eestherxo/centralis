from typing import Any

from flask import Blueprint, request

from app.modules.visitor_management import (
    VisitorManagementError,
    check_in_visitor as manage_check_in,
    check_out_visitor as manage_check_out,
    register_visitor as manage_registration,
)

visitors_bp = Blueprint("visitors", __name__, url_prefix="/visitors")

def _json_body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise VisitorManagementError("A JSON object is required.", 400)
    return data


def _error_response(error: VisitorManagementError):
    response = {"error": str(error)}
    if error.fields:
        response["fields"] = error.fields
    return response, error.status_code


def _visitor_record_id(data: dict[str, Any]) -> int | None:
    visitor_id = data.get("visitor_id")
    if visitor_id is None:
        return None
    if isinstance(visitor_id, int) and not isinstance(visitor_id, bool):
        return visitor_id
    raise VisitorManagementError(
        "Invalid visitor details.",
        400,
        {"visitor_id": "Enter a valid visitor ID."},
    )


# def _optional_visitor_text(data: dict[str, Any], field: str) -> str | None:
#     value = data.get(field)
#     if value is None:
#         return None
#     if not isinstance(value, str):
#         raise VisitorManagementError(
#             "Invalid visitor details.",
#             400,
#             {field: "Enter a valid value."},
#         )
#     return value


def _required_visitor_text(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise VisitorManagementError(
            "Invalid visitor details.",
            400,
            {field: "This field is required."},
        )
    return value


@visitors_bp.post("/register")
def register_visitor():
    try:
        data = _json_body()
        saved_visitor, visit = manage_registration(data)
    except VisitorManagementError as error:
        return _error_response(error)
    return {
        "message": "Visitor registered and checked in successfully.",
        "visitor": saved_visitor,
        "visit": visit,
    }, 201


@visitors_bp.post("/check-in")
def check_in_visitor():
    try:
        data = _json_body()

        
        visit = manage_check_in(
            _required_visitor_text(data, "purpose"),
            int(_required_visitor_text(data, "visitor_id"))
        )
    except VisitorManagementError as error:
        return _error_response(error)
    return {
        "message": "Visitor checked in successfully.",
        "visit": visit,
    }, 201


@visitors_bp.post("/check-out")
def check_out_visitor():
    try:
        data = _json_body()
        updated_visit = manage_check_out(
            int(_required_visitor_text(data, "visitor_id"))
        )
    except VisitorManagementError as error:
        return _error_response(error)
    return {
        "message": "Visitor checked out successfully.",
        "visit": updated_visit,
    }, 200
