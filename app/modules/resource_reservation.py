import json
from datetime import date, datetime, time

from app import data_access
from app.models import (
    ArchivalReservation,
    BookReservation,
    ReservationStatus,
    ResourceCondition,
    ResourceStatus,
    RoomReservation,
)

ONSITE_TYPES = {"room", "archival"}
SUPPORTED_TYPES = ONSITE_TYPES | {"book"}
OPEN_TIME = time(8, 30)
CLOSE_TIME = time(16, 30)


def _has_overlapping_approved_reservation(
    reservation_type: str,
    resource_id: int,
    reserve_date: str,
    start_time: time,
    end_time: time,
) -> bool:
    
    for existing in data_access.get_all_records("reservation"):
        if (
            existing.get("status") != ReservationStatus.APPROVED.value
            or existing.get("reservation_type") != reservation_type
            or existing.get("resource_id") != resource_id
            or existing.get("reserve_date") != reserve_date
        ):
            continue

        existing_start = time.fromisoformat(existing["start_time"])
        existing_end = time.fromisoformat(existing["end_time"])

        if start_time < existing_end and existing_start < end_time:
            return True

    return False


def create_reservation(reservation_type: str, data: dict) -> tuple[dict, int]:
    if reservation_type not in SUPPORTED_TYPES:
        return {"error": "Choose room, archival, or book."}, 400

    visitor_id = data.get("visitor_id")
    resource_id = data.get("resource_id")

    if (
        type(visitor_id) is not int or visitor_id <= 0
        or type(resource_id) is not int or resource_id <= 0
    ):
        return {"error": "A valid visitor_id and resource_id are required."}, 400

    visitor = data_access.get_record("visitor", visitor_id)
    if visitor is None:
        return {"error": "Visitor is not registered."}, 404

    resource = data_access.get_record(reservation_type, resource_id)
    if resource is None:
        return {"error": "Resource not found."}, 404

    if resource.get("status") != ResourceStatus.AVAILABLE.value:
        return {"error": "This resource is not available for requests."}, 409
    if resource.get("condition") != ResourceCondition.GOOD.value:
        return {"error": "Lost or damaged resources cannot be requested."}, 409

    request_base = {
        "visitor": visitor_id,
        "resource": resource_id,
        "request_date": date.today(),
    }

    try:
        if reservation_type in ONSITE_TYPES:
            reserve_date = date.fromisoformat(data.get("reserve_date", ""))
            start_time = time.fromisoformat(data.get("start_time", ""))
            end_time = time.fromisoformat(data.get("end_time", ""))

            if reserve_date.weekday() >= 5:
                return {"error": "Reservations must be Monday through Friday."}, 400
            if not OPEN_TIME <= start_time < end_time <= CLOSE_TIME:
                return {
                    "error": "The reservation must fall between 08:30 and 16:30."
                }, 400

            if _has_overlapping_approved_reservation(
                reservation_type=reservation_type,
                resource_id=resource_id,
                reserve_date=reserve_date.isoformat(),
                start_time=start_time,
                end_time=end_time,
            ):
                return {
                    "error": "This request overlaps an approved reservation."
                }, 409


            if reservation_type == "room":
                occupants = data.get("occupants")
                if type(occupants) is not int or occupants <= 0:
                    return {"error": "occupants must be a positive integer."}, 400
                if occupants > resource.get("capacity", 0):
                    return {"error": "Occupants exceed the room capacity."}, 400

                reservation = RoomReservation(
                    **request_base,
                    start_time=start_time,
                    end_time=end_time,
                    reserve_date=reserve_date,
                    occupants=occupants,
                )
            else:
                reservation = ArchivalReservation(
                    **request_base,
                    start_time=start_time,
                    end_time=end_time,
                    reserve_date=reserve_date,
                )
        else:
            expected_return = date.fromisoformat(data.get("expected_return", ""))
            if expected_return < date.today():
                return {"error": "expected_return cannot be in the past."}, 400

            reservation = BookReservation(
                **request_base,
                expected_return=expected_return,
                actual_return=None,
            )
    except (TypeError, ValueError):
        return {"error": "Dates and times must use ISO format."}, 400

    saved = data_access.create("reservation", reservation.to_dict())
    response = {
        "reservation": saved,
        "visitor": {
            "id": visitor["id"],
            "name": visitor["name"],
            "student_id": visitor.get("student_id"),
            "phone_number": visitor.get("phone_number"),
        },
        "resource": {"id": resource["id"], "name": resource["name"]},
    }
    return response, 201


def approve_reservation(reservation_id: int) -> tuple[dict, int]:

    reservation = data_access.get_record("reservation", reservation_id)
    if reservation is None:
        return {"error": "Reservation not found."}, 404
    if reservation.get("status") != ReservationStatus.PENDING.value:
        return {"error": "Only pending requests can be approved."}, 409

    reservation_type = reservation["reservation_type"]
    resource = data_access.get_record(
        reservation_type,
        reservation["resource_id"],
    )
    if resource is None:
        return {"error": "Resource not found."}, 404
    if (
        resource.get("status") != ResourceStatus.AVAILABLE.value
        or resource.get("condition") != ResourceCondition.GOOD.value
    ):
        return {"error": "This resource is no longer available."}, 409

    if reservation_type in ONSITE_TYPES:
        if _has_overlapping_approved_reservation(
            reservation_type=reservation_type,
            resource_id=reservation["resource_id"],
            reserve_date=reservation["reserve_date"],
            start_time=time.fromisoformat(reservation["start_time"]),
            end_time=time.fromisoformat(reservation["end_time"]),
        ):
            return {
                "error": "This request overlaps an approved reservation."
            }, 409


    updated = data_access.update(
        "reservation",
        reservation_id,
        {"status": ReservationStatus.APPROVED.value},
    )

    if reservation_type == "book":
        data_access.update(
            "book",
            reservation["resource_id"],
            {"status": ResourceStatus.RESERVED.value},
        )

    return updated, 200


def decline_reservation(reservation_id: int) -> tuple[dict, int]:

    reservation = data_access.get_record("reservation", reservation_id)
    if reservation is None:
        return {"error": "Reservation not found."}, 404
    if reservation.get("status") != ReservationStatus.PENDING.value:
        return {"error": "Only pending requests can be declined."}, 409

    updated = data_access.update(
        "reservation",
        reservation_id,
        {"status": ReservationStatus.DECLINED.value},
    )
    return updated, 200


def cancel_reservation(reservation_id: int) -> tuple[dict, int]:

    reservation = data_access.get_record("reservation", reservation_id)
    if reservation is None:
        return {"error": "Reservation not found."}, 404
    if reservation.get("reservation_type") not in ONSITE_TYPES:
        return {"error": "Only room and archival requests can be cancelled."}, 400
    if reservation.get("status") not in {
        ReservationStatus.PENDING.value,
        ReservationStatus.APPROVED.value,
    }:
        return {"error": "This request cannot be cancelled."}, 409

    scheduled_start = datetime.combine(
        date.fromisoformat(reservation["reserve_date"]),
        time.fromisoformat(reservation["start_time"]),
    )
    if scheduled_start <= datetime.now():
        return {
            "error": "Requests can only be cancelled before their start time."
        }, 409

    updated = data_access.update(
        "reservation",
        reservation_id,
        {"status": ReservationStatus.CANCELLED.value},
    )
    return updated, 200


def record_book_return(reservation_id: int, actual_return: str) -> tuple[dict, int]:

    reservation = data_access.get_record("reservation", reservation_id)
    if reservation is None:
        return {"error": "Reservation not found."}, 404
    if reservation.get("reservation_type") != "book":
        return {"error": "This is not a book reservation."}, 400
    if (
        reservation.get("status") != ReservationStatus.APPROVED.value
        or reservation.get("actual_return") is not None
    ):
        return {"error": "This book is not awaiting return."}, 409

    try:
        return_date = date.fromisoformat(actual_return)
    except (TypeError, ValueError):
        return {"error": "actual_return must be an ISO date."}, 400

    updated = data_access.update(
        "reservation",
        reservation_id,
        {"actual_return": return_date},
    )
    data_access.update(
        "book",
        reservation["resource_id"],
        {"status": ResourceStatus.AVAILABLE.value},
    )

    return updated, 200