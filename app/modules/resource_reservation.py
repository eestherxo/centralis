from datetime import date, datetime, time
from app import data_access
from app.models import (
    ArchivalItem,
    Book,
    ResourceCondition,
    ResourceStatus,
    ResourceType,
    ReservationStatus,
    Room,
    OnsitReservation,
    RoomReservation,
    ArchivalReservation,
    BookReservation,
)

RESOURCE_TYPES = {
    ResourceType.BOOK.value: BookReservation,
    ResourceType.ARCHIVAL.value: ArchivalReservation,
    ResourceType.ROOM.value: RoomReservation
}

RESOURCE_STATUS = {
    ResourceStatus.AVAILABLE.value,
    ResourceStatus.RESERVED.value,
}

RESOURCE_CONDITION = {
    ResourceCondition.GOOD.value,
    ResourceCondition.LOST.value,
    ResourceCondition.DAMAGED.value,
}

RESERVATION_STATUS = {
    ReservationStatus.PENDING.value,
    ReservationStatus.APPROVED.value,
    ReservationStatus.DECLINED.value,
    ReservationStatus.CANCELLED.value,
}

RESERVATION_TYPES = {
    "Room Reservation": RoomReservation,
    "Archival Reservation": ArchivalReservation,
    "Book Borrowing": BookReservation,
}

EDITABLE_FIELDS = {
    "room": {"visitor_id", "name", "start_time", "end_time", "date", "occupants"},
    "archival": {"visitor_id", "name", "start_time", "end_time", "date"},
    "book": {"visitor_id", "name", "return_date"}
}

#Placeholder hours
OPEN_TIME = time(9, 0)
CLOSE_TIME = time(17, 0)

#helper functions
def find_resource_by_name(resource_type, resource_name):
    all_resources = data_access.get_all_records(resource_type)
    for r in all_resources:
        if r["name"] == resource_name:
            return r
    return None


#checks for clashing reservations
def check_availability(resource_type, resource_id, start_time, end_time, reservation_date):
    if not isinstance(start_time, time) and not isinstance(end_time, time):
        raise ValueError("Invalid Time Format")

    all_reservations = data_access.get_all_records("reservation")

    for reservation in all_reservations:
        reservation_start = datetime.strptime(reservation.get("start_time"), "%H:%M").time()
        reservation_end = datetime.strptime(reservation.get("end_time"), "%H:%M").time()

        if(reservation.get("resource_type") == resource_type and
           reservation.get("resource_id") == resource_id and
           reservation.get("reservation_date") == reservation_date and
           reservation_start <= end_time and
           reservation_end >= start_time and
           reservation.get("status") == ReservationStatus.APPROVED.value):
            
            return False

    return True

#checks if time is during operating hours
def check_valid_time(start_time, end_time):
    if start_time < OPEN_TIME or end_time > CLOSE_TIME:
        return False
    
    return True

#changes reservation statuses
def change_status(reservation, status):
    if status not in RESERVATION_STATUS:
        raise ValueError("Invalid Status")

    reservation["status"] = status
    return reservation


#main functions for reservation
def make_reservation(resource_type, data):
    model = RESOURCE_TYPES.get(resource_type)
    allowed_fields = EDITABLE_FIELDS.get(model)

    if model is None:
        raise ValueError("Invalid resource type")

    if not isinstance(data, dict) or not data:
        raise ValueError("Invalid reservation data")
    
    unexpected_fields = data.keys() - allowed_fields
    if unexpected_fields:
        raise ValueError(f"Unnecesary fields entered: {sorted(unexpected_fields)}")

    #checks if resource exists
    resource = find_resource_by_name(resource_type, data.get("name"))
    if resource is None:
        raise ValueError("Resource not found")

    #checks resource condition and status check
    condition = resource.get("condition")
    status = resource.get("status")
    if not status in RESOURCE_STATUS:
        raise ValueError("Invalid Resource Status")

    if not condition in RESOURCE_CONDITION:
        raise ValueError("Invalid Resource Condition")

    if condition != ResourceCondition.GOOD.value:
        return "Resource is in Bad Condition"

    if status == ResourceStatus.RESERVED.value:
        return "Resource is Reserved"
    
    #operating hours check
    start_time = data["start_time"]
    end_time = data["end_time"]
    start_time = datetime.strptime(start_time, "%H:%M").time()
    end_time = datetime.strptime(end_time, "%H:%M").time()

    if not check_valid_time(start_time, end_time):
        return "Time is outside of Operating Hours"

    #availability
    resource_id = resource.get("resource_id")
    if not check_availability(resource_type, resource_id, start_time, end_time, data["date"]):
        return "Resource is not Available at Selected Time."

    reservation = model(**data)
    change_status(reservation, ReservationStatus.PENDING.value)
    return data_access.create("reservation", reservation.to_dict()) 


def book_return_date(reservation_id, date_returned): #logs book return date
    reservation = data_access.get_record("reservation", reservation_id)
    reservation["actual_return_date"] = date_returned

    return data_access.update("reservation", reservation_id, reservation)


def cancel_reservation(reservation_type, reservation_id):
    if reservation_type not in RESERVATION_TYPES:
        raise ValueError("Invalid Reservation Type")

    record = data_access.get_record(reservation_type, reservation_id)
    if record is None:
        return None

    reservation = change_status(data_access.get_record("reservation"), ReservationStatus.CANCELLED.value)
    return data_access.update("reservation", reservation_id, reservation)


def accept_deny_reservation(reservation_id, status):
    reservation = data_access.get_record(reservation_id)
    reservation = change_status(reservation, status)

    return data_access.update("reservation", reservation_id, reservation)


def list_reservations(reservation_type = None): #lists reservation based on type, same logic as list_available_resource
    if reservation_types is not None and reservation_types not in RESERVATION_TYPES:
        raise ValueError("Invalid Reservation Types")

    if reservation_type == None:
        reservation_types = RESERVATION_TYPES #all types
    else:
        reservation_types = [reservation_type] #specific types

    available = []
    
    for type in reservation_types:
        records = data_access.get_all_records(type)
        available.extend(
            record
            for record in records
            if record.get("status") == ResourceStatus.AVAILABLE.value
            and record.get("condition") == ResourceCondition.GOOD.value
        )
    
    return available