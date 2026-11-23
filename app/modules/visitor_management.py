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


STUDENT_VISITOR_TYPES = {VisitorType.UNDERGRAD, VisitorType.POSTGRAD}
COMMON_VISITOR_FIELDS = ("name", "phone_number", "purpose")


def _validate_required_fields(data: dict[str, Any], fields: tuple[str, ...]) -> None:
    errors = {
        field: "This field is required."
        for field in fields
        if not isinstance(data.get(field), str) or not data[field].strip()
    }
    if errors:
        raise VisitorManagementError("Invalid visitor details.", 400, errors)

# student ID can be used to find a student at registration to prevent duplicate registration 
def _find_visitor_by_student_id(student_id: str | None) -> dict[str, Any] | None:
    if not isinstance(student_id, str):
        return None
    normalized_id = student_id.strip().casefold()
    return next(
        (
            visitor
            for visitor in data_access.get_all_records("visitor")
            if isinstance(visitor.get("id"), str)
            and visitor["id"].strip().casefold() == normalized_id
        ),
        None,
    )


def _find_visitor(visitor_id: int) -> dict[str, Any] | None:
    return next(
        (
            visitor
            for visitor in data_access.get_all_records("visitor")
            if visitor.get("id") == visitor_id
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
    _validate_required_fields(data, ("type",))
    try:
        visitor_type = VisitorType(data["type"].strip().lower())
    except ValueError as error:
        raise VisitorManagementError(
            "Invalid visitor details.",
            400,
            {"type": "Choose undergraduate, postgraduate, or external."},
        ) from error

    required_fields = COMMON_VISITOR_FIELDS
    if visitor_type in STUDENT_VISITOR_TYPES:
        required_fields += ("student_id", "faculty")
    _validate_required_fields(data, required_fields)

    raw_student_id = data.get("student_id")
    if visitor_type is VisitorType.EXTERNAL:
        if raw_student_id is not None and (
            not isinstance(raw_student_id, str) or raw_student_id.strip()
        ):
            raise VisitorManagementError(
                "Invalid visitor details.",
                400,
                {"student_id": "Only students may provide an ID number."},
            )
        if data.get("faculty") is not None and not isinstance(data["faculty"], str):
            raise VisitorManagementError(
                "Invalid visitor details.",
                400,
                {"faculty": "Enter a valid faculty."},
            )
    # external visitors dont have a student ID so duplicate registration can happen    
    # use a combination of name and phone number to prevent duplicate registration 
    elif _find_visitor_by_student_id(raw_student_id): 
        raise VisitorManagementError(
            "This visitor is already registered. Please check in with the existing record.",
            409,
        )

    purpose = data["purpose"].strip()
    faculty = data.get("faculty")
    student_id = raw_student_id.strip() if isinstance(raw_student_id, str) else None
    visitor = Visitor(
        name=data["name"].strip(),
        phone_number=data["phone_number"].strip(),
        type=visitor_type,
        purpose=purpose,
        faculty=(
            faculty.strip() or None
            if isinstance(faculty, str)
            else None
        ),
        student_id=student_id or None,
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


def _validate_visitor_identifier(visitor_id: int) -> None:
    if visitor_id is not None:
        if (
            isinstance(visitor_id, int)
            and not isinstance(visitor_id, bool)
            and visitor_id > 0
        ):
            return
        raise VisitorManagementError(
            "Invalid visitor details.",
            400,
            {"visitor_id": "Enter a valid visitor ID."},
        )
    


def check_in_visitor(purpose: str, visitor_id: int) -> dict[str, Any]:
    _validate_required_fields({"purpose": purpose}, ("purpose",))
    _validate_visitor_identifier(visitor_id)
    visitor = _find_visitor(visitor_id)
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


def check_out_visitor(visitor_id: int) -> dict[str, Any]:
    _validate_visitor_identifier(visitor_id)
    visitor = _find_visitor(visitor_id)
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