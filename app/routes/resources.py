
from flask import Blueprint, request  # type: ignore[reportMissingImports]
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore[reportMissingImports]
from app.modules import resource_management, authentication

inventory_bp = Blueprint("resource", __name__, url_prefix="/inventory")



@inventory_bp.post("/add")
@jwt_required()
def add_resource_record():

    user_id = get_jwt_identity()
    user = authentication.get_user(user_id)

    if not user or user["role"].lower() != 'admin':
        return {"error": "Only admins can create resource records"}, 403

    resource_type = request.json.get("type", None)
    data = request.json.get("data", None)

    if not resource_type or not data:
        return {"error": "Missing required fields"}, 400

    try:
        record = resource_management.create_resource(resource_type, data)
        return {f"{resource_type}": record}, 201
    except (TypeError, ValueError) as e:
        return {"error": str(e)}, 400


@inventory_bp.put("/<resource_type>/<int:resource_id>")
@jwt_required()
def update_resource_record(resource_type, resource_id):

    user_id = get_jwt_identity()
    user = authentication.get_user(user_id)
    
    if not user or user["role"].lower() != 'admin':
        return {"error": "Only admins can edit resource records"}, 403

    data = request.json.get("data", None)
    
    if not resource_type or not data:
        return {"error": "Missing required fields"}, 400

    try:
        new_record = resource_management.update_resource(resource_type, resource_id, data)

        if new_record is None:
            return {"error": "Resource not found"}, 404

        return {f"{resource_type}": new_record}, 200
    except (TypeError, ValueError) as e:
        return {"error": str(e)}, 400


@inventory_bp.delete("/<resource_type>/<int:resource_id>")
@jwt_required()
def delete_resource_record(resource_type, resource_id):

    user_id = get_jwt_identity()
    user = authentication.get_user(user_id)
    
    if not user or user["role"].lower() != 'admin':
        return {"error": "Only admins can delete resource records"}, 403
    
    try:
        deleted = resource_management.delete_resource(resource_type, resource_id)
    except ValueError as e:
        return {"error": str(e)}, 500

    if deleted is None:
        return {"error": "Resource not found"}, 404
    
    if deleted is False:
        return {"error": "Resource has an active reservation"}, 409

    return {"message": "Resource deleted"}, 200


@inventory_bp.get("/available")
def get_available_resources():
    resource_type = request.args.get("type")

    try:
        records = resource_management.list_available_resources(resource_type)
        return {"resources": records}, 200
    except ValueError as e:
        return {"error": str(e)}, 500



