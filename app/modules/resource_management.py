from app import data_access
from app.models import (
    ArchivalItem,
    Book,
    Journal,
    ResourceCondition,
    ResourceStatus,
    ResourceType,
    ReservationStatus,
    Room,
)

RESOURCE_MODELS = {
    ResourceType.BOOK.value: Book,
    ResourceType.JOURNAL.value: Journal,
    ResourceType.ARCHIVAL.value: ArchivalItem,
    ResourceType.ROOM.value: Room
}

EDITABLE_FIELDS = {
    "book": {"name", "author", "price", "genre", "status", "condition"},
    "journal": {"name", "author", "price", "stock", "status", "condition"},
    "archival": {"name", "status", "condition"},
    "room": {"name", "capacity", "status", "condition"},
}

ACTIVE_RESERVATION_STATUSES = {
    ReservationStatus.PENDING.value,
    ReservationStatus.APPROVED.value,
}


def create_resource(resource_type, data):

    model = RESOURCE_MODELS.get(resource_type)
    if model is None:
        raise ValueError("Invalid resource type")
    if not isinstance(data, dict):
        raise ValueError("Resource data must be JSON format")

    resource = model(**data)
    return data_access.create(resource_type, resource.to_dict())
    

def update_resource(resource_type, resource_id, new_data):
    allowed_fields = EDITABLE_FIELDS.get(resource_type)
    if allowed_fields is None:
        raise ValueError("Invalid resource type")
    if not isinstance(new_data, dict) or not new_data:
        raise ValueError("Provide at least one field to update")

    unexpected_fields = new_data.keys() - allowed_fields
    if unexpected_fields:
        raise ValueError(f"Fields cannot be updated: {sorted(unexpected_fields)}")


    for field, enum_type in (
        ("status", ResourceStatus),
        ("condition", ResourceCondition),
    ):
        if field in new_data:
            try:
                enum_type(new_data[field]).value
            except (TypeError, ValueError):
                raise ValueError(f"Invalid {field}")

    old_record = data_access.get_record(resource_type, resource_id)

    if old_record:
        new_record = data_access.update(resource_type, resource_id, new_data)
        return new_record
        
    return None



def delete_resource(resource_type, resource_id):
    if resource_type not in RESOURCE_MODELS:
        raise ValueError("Invalid resource type")

    record = data_access.get_record(resource_type, resource_id)
    if record is None:
        return None

    reservations = data_access.get_all_records("reservation")
    has_active_reservation = False

    for reservation in reservations:
        matches_resource = (
            reservation.get("resource_id") == resource_id
            and reservation.get("reservation_type") == resource_type
        )
        is_active = reservation.get("status") in ACTIVE_RESERVATION_STATUSES
        if matches_resource and is_active:
            has_active_reservation = True
            break 
    
    if has_active_reservation:
        return False

    return data_access.delete(resource_type, resource_id)


def list_available_resources(resource_type=None):
    if resource_type is not None and resource_type not in RESOURCE_MODELS:
        raise ValueError("Invalid resource type")

    if resource_type is None:
        resource_types = RESOURCE_MODELS # search all types 
    else:
        resource_types = [resource_type] # search only the requested type
    available = []

    for rtype in resource_types:
        records = data_access.get_all_records(rtype)
        available.extend(
            record
            for record in records
            if record.get("status") == ResourceStatus.AVAILABLE.value
            and record.get("condition") == ResourceCondition.GOOD.value
        )

    return available
