from data_access import get_all_records, get_record, create, update, delete
from models import Book, Journal, ArchivalItem, Room
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.post("/add")
def add_resource_record():

    # TODO: Implement access control to ensure only admin users can add records

    resource_type = request.json.get("type", None)
    resource_data = request.json.get("data", None)

    if not resource_type or not resource_data:
        return {"error": "Missing required fields"}, 400

    if resource_type == "book":
        resource = Book(**resource_data)
    elif resource_type == "journal":
        resource = Journal(**resource_data)
    elif resource_type == "archival":
        resource = ArchivalItem(**resource_data)
    elif resource_type == "room":
        resource = Room(**resource_data)
    else:
        return {"error": "Invalid resource type"}, 400

    try:
        create(resource.category.value, resource.to_dict())
        return {"message": f"{resource_type.capitalize()} added successfully."}, 201
    except Exception as e:
        return {"error": str(e)}, 500


@inventory_bp.get("/<resource_type>")
def get_all_resource_records(resource_type):

    if resource_type not in ["book", "journal", "archival", "room"]:
        return {"error": "Invalid resource type"}, 400

    try:
        records = get_all_records(f"{resource_type}s")
        return {f"{resource_type}": records}, 200
    except Exception as e:
        return {"error": str(e)}, 500


@inventory_bp.get("/<resource_type>/<int:resource_id>")
def get_resource_record(resource_type, resource_id):

    if resource_type not in ["book", "journal", "archival", "room"]:
        return {"error": "Invalid resource type"}, 400

    try:
        record = get_record(f"{resource_type}s", resource_id)
        if record:
            return {f"{resource_type}": record}, 200
        else:
            return {"error": f"{resource_type.capitalize()} not found"}, 404
    except Exception as e:
        return {"error": str(e)}, 500


@inventory_bp.put("/<resource_type>/<int:resource_id>")
def update_resource_record(resource_type, resource_id):

    # TODO: Implement access control to ensure only admin users can update records

    if resource_type not in ["book", "journal", "archival", "room"]:
        return {"error": "Invalid resource type"}, 400

    new_record = request.json.get("data", None)
    if not new_record:
        return {"error": "Missing required fields"}, 400

    try:
        updated_record = update(f"{resource_type}s", resource_id, new_record)
        if updated_record:
            return {f"{resource_type}": updated_record}, 200
        else:
            return {"error": f"{resource_type.capitalize()} not found"}, 404
    except Exception as e:
        return {"error": str(e)}, 500
