from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.modules import journal_sales, authentication

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


def is_staff_or_admin():
    user = authentication.get_user(get_jwt_identity())
    return user is not None and user["role"].lower() in ("staff", "admin")


@sales_bp.post("")
@jwt_required()
def record_sale():
    if not is_staff_or_admin():
        return {"error": "Only staff and admins can record journal sales"}, 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "Missing required fields"}, 400

    try:
        sale = journal_sales.record_sale(
            data.get("journal_id"), data.get("quantity"), data.get("date_sold")
        )
    except ValueError as e:
        return {"error": str(e)}, 400

    sale["date_sold"] = sale["date_sold"].isoformat()
    return {"message": "Journal sale recorded", "sale": sale}, 201


@sales_bp.get("")
@jwt_required()
def list_sales():
    if not is_staff_or_admin():
        return {"error": "Only staff and admins can view journal sales"}, 403

    return {"sales": journal_sales.list_sales()}, 200


@sales_bp.post("/<int:sale_id>/confirm-payment")
@jwt_required()
def confirm_payment(sale_id):
    if not is_staff_or_admin():
        return {"error": "Only staff and admins can confirm payments"}, 403

    try:
        sale = journal_sales.confirm_payment(sale_id)
    except ValueError as e:
        return {"error": str(e)}, 404

    return {"message": "Payment confirmed", "sale": sale}, 200


@sales_bp.get("/<int:sale_id>/receipt")
@jwt_required()
def get_receipt(sale_id):
    if not is_staff_or_admin():
        return {"error": "Only staff and admins can generate receipts"}, 403

    try:
        receipt = journal_sales.generate_receipt(sale_id)
    except ValueError as e:
        if "not found" in str(e):
            return {"error": str(e)}, 404
        return {"error": str(e)}, 409

    return {"receipt": receipt}, 200
