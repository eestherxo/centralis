from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.modules import resource_fines

fines_bp = Blueprint("fines", __name__, url_prefix="/fines")


def error_response(error):
    # Assign HTTP status codes based on the type of error
    if isinstance(error, resource_fines.PermissionDenied):
        return {"error": str(error)}, 403
    if isinstance(error, resource_fines.FineNotFound):
        return {"error": str(error)}, 404
    if isinstance(error, resource_fines.PaymentNotConfirmed):
        return {"error": str(error)}, 409
    return {"error": str(error)}, 400


def json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@fines_bp.post("/returns")
@jwt_required()
def record_return():
    data = json_body()
    if data is None:
        return {"error": "Missing required fields"}, 400

    try:
        result = resource_fines.record_return(
            get_jwt_identity(),
            data.get("reservation_id"),
            data.get("return_date"),
            data.get("condition", "good"),
        )
    except ValueError as e:
        return error_response(e)

    message = "Return recorded. A fine is owed" if result["fines"] else "Return recorded. No fine is owed"
    return {"message": message, **result}, 201


@fines_bp.post("/lost-or-damaged")
@jwt_required()
def lost_or_damaged():
    data = json_body()
    if data is None:
        return {"error": "Missing required fields"}, 400

    try:
        fine = resource_fines.lost_or_damaged(
            get_jwt_identity(),
            data.get("resource_id"),
            data.get("condition"),
            data.get("visitor_id"),
        )
    except ValueError as e:
        return error_response(e)

    return {"message": "Fine recorded", "fine": fine}, 201


@fines_bp.get("")
@jwt_required()
def list_fines():
    try:
        fines = resource_fines.list_fines(get_jwt_identity(), request.args.get("status"))
    except ValueError as e:
        return error_response(e)

    return {"fines": fines}, 200


@fines_bp.get("/loans")
@jwt_required()
def active_loans():
    try:
        loans = resource_fines.active_loans(get_jwt_identity())
    except ValueError as e:
        return error_response(e)

    return {"loans": loans}, 200


@fines_bp.get("/visitors")
@jwt_required()
def list_visitors():
    try:
        visitors = resource_fines.list_visitors(get_jwt_identity())
    except ValueError as e:
        return error_response(e)

    return {"visitors": visitors}, 200


@fines_bp.get("/resources")
@jwt_required()
def resources_condition():
    try:
        resources = resource_fines.resources_condition(get_jwt_identity())
    except ValueError as e:
        return error_response(e)

    return {"resources": resources}, 200


@fines_bp.get("/visitor/<int:visitor_id>/unpaid")
@jwt_required()
def unpaid_fines(visitor_id):
    try:
        fines = resource_fines.unpaid_fines(get_jwt_identity(), visitor_id)
    except ValueError as e:
        return error_response(e)

    return {"fines": fines}, 200


@fines_bp.post("/<int:fine_id>/confirm-payment")
@jwt_required()
def confirm_payment(fine_id):
    try:
        fine = resource_fines.confirm_payment(get_jwt_identity(), fine_id)
    except ValueError as e:
        return error_response(e)

    return {"message": "Payment confirmed", "fine": fine}, 200


@fines_bp.get("/<int:fine_id>/receipt")
@jwt_required()
def get_receipt(fine_id):
    try:
        pdf = resource_fines.generate_receipt_pdf(get_jwt_identity(), fine_id)
    except ValueError as e:
        return error_response(e)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"fine-receipt-{fine_id}.pdf",
    )
