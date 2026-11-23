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
    ResourceType.BOOK.value: Book,
    ResourceType.ARCHIVAL.value: ArchivalItem,
    ResourceType.ROOM.value: Room
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
    "room": {"name", "start time", "end time", "date", "occupants"},
    "archival": {"name", "start time", "end time", "date"},
    "book": {"name", "return date"}
}

#Placeholder hours
OPEN_TIME = time(8, 30)
CLOSE_TIME = time(16, 10)

#helper functions
def find_resource_by_name(resource_type, resource_name):
    all_resources = data_access.get_all_records(resource_type)
    for r in all_resources:
        if r["name"] == resource_name:
            return r
    return None

#main functions
def make_request(resource_type, data):
    #currently creates request and doesn't check if availability or condition
    model = RESOURCE_TYPES.get(resource_type)
    allowed_fields = EDITABLE_FIELDS.get(model)

    #checks if resource type exists
    if model is None:
        raise ValueError("Invalid resource type")

    #checks data
    if not isinstance(data, dict) or not data:
        raise ValueError("Invalid reservation data")
    
    unexpected_fields = data.keys() - allowed_fields
    if unexpected_fields:
        raise ValueError(f"Unnecesary fields entered: {sorted(unexpected_fields)}")

    #checks if resource exists
    resource = find_resource_by_name(resource_type, data["name"])
    if resource is None:
        raise ValueError("Resource not found")

    reservation = model(**data)
    return data_access.create("request", reservation.to_dict()) 


def set_book_return(book_id, date_returned):
    if not isinstance(date_returned, date):
        raise ValueError("Not a valid date")
    
    book = data_access.get_record(Book, book_id)
    book["return date"] = date_returned

def request_management():
    pass

def set_status():
    pass

def cancel_request(reservation_type, reservation_id):
    if reservation_type not in RESERVATION_TYPES:
        raise ValueError("Invalid Reservation Type")

    record = data_access.get_record(reservation_type, reservation_id)
    if record is None:
        return None

    return data_access.delete(reservation_type, reservation_id)