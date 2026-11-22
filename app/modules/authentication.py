import bcrypt

from app import data_access
from app.models import Role, User



def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }


def create_user(data: dict) -> tuple[dict, int]:
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role_value = data.get("role", Role.STAFF.value)

    if not all(
        isinstance(value, str)
        for value in (name, email, password, role_value)
    ):
        return {"error": "Invalid account details."}, 400

    if not name.strip() or not email.strip():
        return {
            "error": "Enter a name, email and a password"
        }, 400

    try:
        role = Role(role_value)
    except ValueError:
        return {"error": "Role must be 'admin' or 'staff'."}, 400

    email = email.strip().casefold()
    users = data_access.get_all_records("user")

    if any(user.get("email", "").casefold() == email for user in users):
        return {"error": "An account with that email already exists."}, 409

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("ascii")

    user = User(
        name=name.strip(),
        email=email,
        password=password_hash,
        role=role,
    )
    return data_access.create("user", user.to_dict()), 201


def authenticate_user(email: object, password: object) -> tuple[dict, int]:
    if not isinstance(email, str) or not isinstance(password, str):
        return {"error": "Invalid email or password."}, 401

    normalized_email = email.strip().casefold()
    user = next(
        (
            record
            for record in data_access.get_all_records("user")
            if record.get("email", "").casefold() == normalized_email
        ),
        None,
    )

    if user is None or not bcrypt.checkpw(
        password.encode("utf-8"),
        user["password"].encode("ascii"),
    ):
        return {"error": "Invalid email or password."}, 401

    return user, 200


def get_user(user_id: int) -> dict | None:
    try:
        normalized_user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    
    return data_access.get_record("user", normalized_user_id)