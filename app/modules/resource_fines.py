from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app import data_access
from app.models import (
    Fine,
    FineReason,
    FineStatus,
    ReservationStatus,
    ResourceCondition,
    ResourceStatus,
    ResourceType,
)
from app.modules import authentication, resource_management
#late fine is 50 per day
LATE_FINE_PER_DAY = 50
#set of resource types that can be fined
RESOURCE_TYPES = [t.value for t in ResourceType]
#the roles that are allowed to manage fines. Only staff and admin accounts can do this
STAFF_ROLES = ("staff", "admin")

#    Errors related to fines
class FineError(ValueError):
    """Base class for every error this module raises on purpose"""


class PermissionDenied(FineError):
    """The user is not authorized SALISES staff (the route sends 403)"""


class FineNotFound(FineError):
    """The record the request points to does not exist (the route sends 404)"""


class PaymentNotConfirmed(FineError):
    """A receipt was asked for before the fine was paid (the route sends 409)"""


##      Helper Functions

def _today():
    # Kept in one place so tests can set the date
    return date.today()


def _require_staff(logged_in_user_id):
    # Only authorized SALISES staff (staff or admin accounts) may change fines
    user = authentication.get_user(logged_in_user_id)
    if user is None or str(user.get("role", "")).lower() not in STAFF_ROLES:
        raise PermissionDenied("Only authorized SALISES staff can manage fines")
    return user


def _to_date(value, label):
    # Accepts a date or text like "2026-11-17"
    if value is None: #no date given, so use today
        return _today()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a valid date (YYYY-MM-DD)") 
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label} must be a valid date (YYYY-MM-DD)") 


def _is_whole_number(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _get(collection, record_id, label):
    if not _is_whole_number(record_id):
        raise ValueError(f"A valid {label.lower()} is required")

    record = data_access.get_record(collection, record_id)
    if record is None:
        raise FineNotFound(f"{label} not found")
    return record


def _find_resource(resource_id):
    # This finds the resource record and its type, or raises FineNotFound if it doesn't exist
    if not _is_whole_number(resource_id):
        raise ValueError("A valid resource is required")

    for resource_type in RESOURCE_TYPES:
        record = data_access.get_record(resource_type, resource_id)
        if record is not None:
            return resource_type, record

    raise FineNotFound("Resource not found")


def _is_active_loan(reservation):
    # An approved book loan that has not been returned yet. If the book was
    # marked lost or damaged, the loan is finished too (the borrower is fined)
    if not (
        reservation.get("reservation_type") == ResourceType.BOOK.value
        and reservation.get("status") == ReservationStatus.APPROVED.value
        and not reservation.get("actual_return")
    ):
        return False

    book = data_access.get_record(ResourceType.BOOK.value, reservation.get("resource_id"))
    return book is not None and book.get("condition", ResourceCondition.GOOD.value) == "good"


def _active_loan_for(resource_id):
    for reservation in data_access.get_all_records("reservation"):
        if reservation.get("resource_id") == resource_id and _is_active_loan(reservation):
            return reservation
    return None


def calculate_fine(expectedDate, actualDate):
    """
    Calculate the fine based on the expected and actual return dates.

    :param expectedDate: The date when the resource was expected to be returned.
    :param actualDate: The date when the resource was actually returned.
    :return: The calculated fine amount.
    """
    if actualDate <= expectedDate:
        return 0
    days_late = max(0, (actualDate - expectedDate).days)
    return days_late * LATE_FINE_PER_DAY


def calculate_late_fine(expected_return, actual_return):
    # Same rule as calculate_fine, but also says how many days late it was
    days_late = max(0, (actual_return - expected_return).days)
    return days_late, float(calculate_fine(expected_return, actual_return))


def _replacement_cost(resource):
    # A lost or damaged resource is charged what it costs to replace it
    price = resource.get("price")
    if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
        raise ValueError(
            f"{resource['name']} has no price recorded, so a replacement fine "
            "cannot be worked out"
        )
    return float(price)


def _new_fine(visitor_id, resource_id, reason, amount):
    # Builds and saves one fine record. New fines always start as unpaid
    fine = Fine(
        visitor=visitor_id,
        resource=resource_id,
        reason=reason,
        amount=round(amount, 2),
        date_issued=_today(),
    )
    created = data_access.create("fine", fine.to_dict())

    # Read it back so the caller gets plain text values, not enums and dates
    return data_access.get_record("fine", created["id"])


def _undo_fines(fines):
    # Put the records back the way they were if a later save fails
    for fine in fines:
        data_access.delete("fine", fine["id"])


def _describe(fine):
    # The fine plus the visitor and resource names a screen needs
    visitor = data_access.get_record("visitor", fine["visitor_id"]) or {}
    resource = {}
    for resource_type in RESOURCE_TYPES:
        resource = data_access.get_record(resource_type, fine["resource_id"])
        if resource:
            break

    return {
        **fine,
        "visitor_name": visitor.get("name", "Unknown visitor"),
        "resource_name": (resource or {}).get("name", "Unknown resource"),
    }


#  Recording returns and lost / damaged resources

def record_return(logged_in_user_id, reservation_id, return_date=None, condition="good"):
    _require_staff(logged_in_user_id)

    if condition not in (ResourceCondition.GOOD.value, ResourceCondition.DAMAGED.value):
        raise ValueError("A returned resource must be good or damaged")

    reservation = _get("reservation", reservation_id, "Loan")
    if not _is_active_loan(reservation):
        raise ValueError("This loan is not active, so it cannot be returned")
    if not reservation.get("expected_return"):
        raise ValueError("This loan has no expected return date")

    resource_type = reservation["reservation_type"]
    resource = _get(resource_type, reservation["resource_id"], "Resource")

    actual_return = _to_date(return_date, "Return date")
    expected_return = _to_date(reservation["expected_return"], "Expected return date")

    # Work out every charge before saving anything
    charges = []
    days_late, late_amount = calculate_late_fine(expected_return, actual_return)
    if late_amount:
        charges.append((FineReason.LATE, late_amount))
    if condition == ResourceCondition.DAMAGED.value:
        charges.append((FineReason.DAMAGED, _replacement_cost(resource)))

    fines = []
    try:
        for reason, amount in charges:
            fines.append(
                _new_fine(reservation["visitor_id"], resource["id"], reason, amount)
            )

        # Write the return date and condition to the reservation and resource records
        updated_reservation = data_access.update(
            "reservation", reservation_id, {"actual_return": actual_return.isoformat()}
        )
        data_access.update(
            resource_type,
            resource["id"],
            {"status": ResourceStatus.AVAILABLE.value, "condition": condition},
        )
    except Exception:
        _undo_fines(fines)
        raise

    return {"reservation": updated_reservation, "fines": fines}

def lost_or_damaged(logged_in_user_id, resource_id, condition, visitor_id=None):
    _require_staff(logged_in_user_id)

    if condition not in (ResourceCondition.LOST.value, ResourceCondition.DAMAGED.value):
        raise ValueError("Condition must be lost or damaged")

    resource_type, resource = _find_resource(resource_id)
    if resource.get("condition", ResourceCondition.GOOD.value) != ResourceCondition.GOOD.value:
        raise ValueError(f"{resource['name']} is already marked {resource['condition']}")

    # Allows staff to select the responsible borrower if the resource is still on loan, or to specify a visitor if it is not
    loan = _active_loan_for(resource_id)
    if visitor_id is None:
        if loan is None:
            raise ValueError("Select the responsible borrower for this resource")
        visitor_id = loan["visitor_id"]
    _get("visitor", visitor_id, "Visitor")

    cost = _replacement_cost(resource)

    fine = _new_fine(visitor_id, resource_id, FineReason(condition), cost)

    try:
        resource_management.update_resource(resource_type, resource_id, {"condition": condition})
    except Exception:
        _undo_fines([fine])
        raise

    return fine


#  Viewing overviews of fines, loans, and visitors

def unpaid_fines(logged_in_user_id, visitor_id):
    _require_staff(logged_in_user_id)
    _get("visitor", visitor_id, "Visitor")

    unpaid = [
        fine
        for fine in data_access.get_all_records("fine")
        if fine["visitor_id"] == visitor_id and fine["status"] == FineStatus.UNPAID.value
    ]
    unpaid.sort(key=lambda fine: (fine["date_issued"], fine["id"]))
    return [_describe(fine) for fine in unpaid]


def list_fines(logged_in_user_id, status=None):
    _require_staff(logged_in_user_id)

    if status is not None and status not in [s.value for s in FineStatus]:
        raise ValueError("Status must be paid or unpaid")

    fines = [
        fine
        for fine in data_access.get_all_records("fine")
        if status is None or fine["status"] == status
    ]
    fines.sort(key=lambda fine: fine["id"], reverse=True)
    return [_describe(fine) for fine in fines]


def active_loans(logged_in_user_id):
    # Loans still waiting to be returned, with how late each one is today
    _require_staff(logged_in_user_id)

    rows = []
    for loan in data_access.get_all_records("reservation"):
        if not _is_active_loan(loan) or not loan.get("expected_return"):
            continue
        days_late, fine_so_far = calculate_late_fine(
            _to_date(loan["expected_return"], "Expected return date"), _today()
        )
        resource = data_access.get_record(loan["reservation_type"], loan["resource_id"]) or {}
        visitor = data_access.get_record("visitor", loan["visitor_id"]) or {}
        rows.append(
            {
                **loan,
                "resource_name": resource.get("name", "Unknown resource"),
                "visitor_name": visitor.get("name", "Unknown visitor"),
                "days_late": days_late,
                "fine_so_far": fine_so_far,
            }
        )

    rows.sort(key=lambda row: row["expected_return"])
    return rows


def list_visitors(logged_in_user_id):
    # Used to pick borrower
    _require_staff(logged_in_user_id)

    return [
        {"id": v["id"], "name": v.get("name"), "type": v.get("type")}
        for v in data_access.get_all_records("visitor")
    ]


def resources_condition(logged_in_user_id):
    # Resources that can still be marked lost or damaged: good condition and a price
    _require_staff(logged_in_user_id)

    rows = []
    for resource_type in RESOURCE_TYPES:
        for resource in data_access.get_all_records(resource_type):
            price = resource.get("price")
            if resource.get("condition", ResourceCondition.GOOD.value) == "good" and price:
                rows.append(
                    {
                        "id": resource["id"],
                        "type": resource_type,
                        "name": resource["name"],
                        "price": price,
                    }
                )
    return rows


# recording payments and generating receipts

def confirm_payment(logged_in_user_id, fine_id):
    _require_staff(logged_in_user_id)

    fine = _get("fine", fine_id, "Fine")
    if fine["status"] == FineStatus.PAID.value:
        raise ValueError("This fine has already been paid")

    return data_access.update(
        "fine",
        fine_id,
        {"status": FineStatus.PAID.value, "date_paid": _today().isoformat()},
    )


def generate_receipt(logged_in_user_id, fine_id):
    _require_staff(logged_in_user_id)

    fine = _get("fine", fine_id, "Fine")

    # Receipts are only given once staff have confirmed payment
    if fine["status"] != FineStatus.PAID.value:
        raise PaymentNotConfirmed("Payment has not been confirmed")

    details = _describe(fine)
    return {
        "receipt_number": fine["id"],
        "visitor_name": details["visitor_name"],
        "resource_name": details["resource_name"],
        "fine_type": fine["reason"],
        "amount_paid": fine["amount"],
        "payment_date": fine["date_paid"],
    }


def _issue_receipt(receipt):
    # Draws the receipt dict from generate_receipt as a PDF and returns it
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 80, "SALISES")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 100, "Fine Payment Receipt")
    pdf.line(60, height - 115, width - 60, height - 115)

    details = [
        ("Receipt number", receipt["receipt_number"]),
        ("Visitor", receipt["visitor_name"]),
        ("Resource", receipt["resource_name"]),
        ("Fine type", receipt["fine_type"].capitalize()),
        ("Amount paid", f"${receipt['amount_paid']:,.2f}"),
        ("Payment date", receipt["payment_date"]),
    ]
    y = height - 160
    for label, value in details:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(70, y, f"{label}:")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(230, y, str(value))
        y -= 30

    pdf.line(60, y, width - 60, y)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(70, y - 30, "Payment received - confirmed by SALISES staff")

    pdf.save()
    buffer.seek(0)
    return buffer


def generate_receipt_pdf(logged_in_user_id, fine_id):
    # generate_receipt applies the rules (staff only, payment confirmed first)
    return _issue_receipt(generate_receipt(logged_in_user_id, fine_id))
