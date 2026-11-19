from flask import Blueprint, request

from app.modules.visitor_management import (
    VisitorManagementError,
    check_in_visitor as manage_check_in,
    check_out_visitor as manage_check_out,
    register_visitor as manage_registration,
)

visitors_bp = Blueprint("visitors", __name__, url_prefix="/visitors")

def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, ({"error": "A JSON object is required."}, 400)
    return data, None


def _error_response(error: VisitorManagementError):
    response = {"error": str(error)}
    if error.fields:
        response["fields"] = error.fields
    return response, error.status_code


@visitors_bp.post("/register")
def register_visitor():
    data, error_response = _json_body()
    if error_response:
        return error_response
    try:
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
    data, error_response = _json_body()
    if error_response:
        return error_response
    try:
        visit = manage_check_in(data.get("id_number"), data.get("purpose"))
    except VisitorManagementError as error:
        return _error_response(error)
    return {
        "message": "Visitor checked in successfully.",
        "visit": visit,
    }, 201


@visitors_bp.post("/check-out")
def check_out_visitor():
    data, error_response = _json_body()
    if error_response:
        return error_response
    try:
        updated_visit = manage_check_out(data.get("id_number"))
    except VisitorManagementError as error:
        return _error_response(error)
    return {
        "message": "Visitor checked out successfully.",
        "visit": updated_visit,
    }, 200
