from datetime import date, datetime, time

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Role
from app.modules import authentication
from app.modules.resource_reservation import (
    approve_reservation as approve_request,
    cancel_reservation as cancel_request,
    create_reservation as submit_request,
    decline_reservation as decline_request,
    record_book_return,
)

reservations_bp = Blueprint(
    "reservations",
    __name__,
    url_prefix="/reservations",
)


def _current_user():
    return authentication.get_user(get_jwt_identity())


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _json_compatible(value):
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    return value


def _service_response(result):
    payload, status = result
    return jsonify(_json_compatible(payload)), status


@reservations_bp.post("/<reservation_type>")
@jwt_required()
def create_reservation(reservation_type: str):
    staff = _current_user()
    if staff is None:
        return {"error": "User account not found."}, 401
    if staff.get("role") != Role.STAFF.value:
        return {"error": "Only staff can submit requests."}, 403

    data = _body()
    if data is None:
        return {"error": "A JSON object is required."}, 400

    return _service_response(submit_request(reservation_type, data))


@reservations_bp.post("/<int:reservation_id>/approve")
@jwt_required()
def approve(reservation_id: int):
    admin = _current_user()
    if admin is None:
        return {"error": "User account not found."}, 401
    if admin.get("role") != Role.ADMIN.value:
        return {"error": "Only an administrator can approve requests."}, 403

    return _service_response(approve_request(reservation_id))


@reservations_bp.post("/<int:reservation_id>/decline")
@jwt_required()
def decline(reservation_id: int):
    admin = _current_user()
    if admin is None:
        return {"error": "User account not found."}, 401
    if admin.get("role") != Role.ADMIN.value:
        return {"error": "Only an administrator can decline requests."}, 403

    return _service_response(decline_request(reservation_id))


@reservations_bp.post("/<int:reservation_id>/cancel")
@jwt_required()
def cancel(reservation_id: int):
    staff = _current_user()
    if staff is None:
        return {"error": "User account not found."}, 401
    if staff.get("role") != Role.STAFF.value:
        return {"error": "Only staff can cancel requests."}, 403

    return _service_response(cancel_request(reservation_id))


@reservations_bp.post("/<int:reservation_id>/return")
@jwt_required()
def return_book(reservation_id: int):
    staff = _current_user()
    if staff is None:
        return {"error": "User account not found."}, 401
    if staff.get("role") != Role.STAFF.value:
        return {"error": "Only staff can record book returns."}, 403

    data = _body()
    if data is None:
        return {"error": "A JSON object is required."}, 400

    return _service_response(record_book_return(reservation_id, data.get("actual_return")))
