from datetime import datetime, timezone
from typing import Any

from app import data_access
from app.models import Visitor, VisitorType


class VisitorManagementError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int,
        fields: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.fields = fields


VISITOR_FIELDS = ("name", "phone_number", "id_number", "faculty", "purpose", "type")


def _validate_required_fields(data: dict[str, Any], fields: tuple[str, ...]) -> None:
    errors = {
        field: "This field is required."
        for field in fields
        if not isinstance(data.get(field), str) or not data[field].strip()
    }
    if errors:
        raise VisitorManagementError("Invalid visitor details.", 400, errors)


def _find_visitor(id_number: str) -> dict[str, Any] | None:
    normalized_id = id_number.strip().casefold()
    return next(
        (
            visitor
            for visitor in data_access.get_all_records("visitor")
            if isinstance(visitor.get("id_number"), str)
            and visitor["id_number"].strip().casefold() == normalized_id
        ),
        None,
    )


def _active_visit(visitor_id: int) -> dict[str, Any] | None:
    return next(
        (
            visit
            for visit in data_access.get_all_records("visit")
            if visit["visitor_id"] == visitor_id and visit["check_out"] is None
        ),
        None,
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_visitor(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    _validate_required_fields(data, VISITOR_FIELDS)
    try:
        visitor_type = VisitorType(data["type"].strip().lower())
    except ValueError as error:
        raise VisitorManagementError(
            "Invalid visitor details.",
            400,
            {"type": "Choose undergraduate, postgraduate, or external."},
        ) from error

    if _find_visitor(data["id_number"]):
        raise VisitorManagementError(
            "This visitor is already registered. Please check in with the existing record.",
            409,
        )

    purpose = data["purpose"].strip()
    visitor = Visitor(
        name=data["name"].strip(),
        phone_number=data["phone_number"].strip(),
        type=visitor_type,
        purpose=purpose,
        faculty=data["faculty"].strip(),
        id_number=data["id_number"].strip(),
    )
    saved_visitor = data_access.create("visitor", visitor.to_dict())
    visit = data_access.create(
        "visit",
        {
            "visitor_id": saved_visitor["id"],
            "purpose": purpose,
            "check_in": _timestamp(),
            "check_out": None,
        },
    )
    return saved_visitor, visit


def check_in_visitor(id_number: str, purpose: str) -> dict[str, Any]:
    _validate_required_fields(
        {"id_number": id_number, "purpose": purpose}, ("id_number", "purpose")
    )
    visitor = _find_visitor(id_number)
    if visitor is None:
        raise VisitorManagementError(
            "Visitor is not registered. Please register first.", 404
        )
    if _active_visit(visitor["id"]):
        raise VisitorManagementError(
            "Visitor already has an active check-in.", 409
        )

    return data_access.create(
        "visit",
        {
            "visitor_id": visitor["id"],
            "purpose": purpose.strip(),
            "check_in": _timestamp(),
            "check_out": None,
        },
    )


def check_out_visitor(id_number: str) -> dict[str, Any]:
    _validate_required_fields({"id_number": id_number}, ("id_number",))
    visitor = _find_visitor(id_number)
    if visitor is None:
        raise VisitorManagementError("Visitor is not registered.", 404)

    visit = _active_visit(visitor["id"])
    if visit is None:
        raise VisitorManagementError(
            "Visitor has no active check-in to check out.", 409
        )

    updated_visit = data_access.update(
        "visit", visit["id"], {"check_out": _timestamp()}
    )
    if updated_visit is None:
        raise VisitorManagementError(
            "The active visit could not be updated.", 500
        )
    return updated_visit