
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import data_access
from app.models import Role
from app.modules.authentication import (
    authenticate_user,
    create_user,
    public_user,
    get_user
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")




@auth_bp.post("/login")
def login():
    data = request.get_json()
    if data is None:
        return {"error": "Missing required fields"}, 400

    user, status = authenticate_user(
        data.get("email"),
        data.get("password"),
    )
    if status != 200:
        return user, status

    token = create_access_token(identity=str(user["id"]))
    return {"access_token": token, "user": public_user(user)}, 200


@auth_bp.post("/users")
@jwt_required()
def register_user():
    user_id = get_jwt_identity()
    creator = get_user(user_id)
    if creator is None:
        return {"error": "User account does not exists."}, 401

    if creator["role"] != Role.ADMIN.value:
        return {"error": "Only an admin can create accounts."}, 403

    data = request.get_json()
    if data is None:
        return {"error": "Mising required fields"}, 400

    user, status = create_user(data)
    if status != 201:
        return user, status

    return {"user": public_user(user)}, 201