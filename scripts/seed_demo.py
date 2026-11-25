"""Insert repeatable demo records for manually testing the Centralis UI.

Run from the repository root with ``python -m scripts.seed_demo``.
Records are reused by their demo email or name.
Demo accounts: admin@salises.test / AdminPass123 and
staff@salises.test / StaffPass123.
"""

from datetime import date, timedelta

from app import data_access
from app.modules.authentication import create_user


def _get_or_create(collection, field, value, record):
    existing = next(
        (item for item in data_access.get_all_records(collection)
         if item.get(field) == value),
        None,
    )
    return existing or data_access.create(collection, record)


def _next_weekday(days_ahead):
    scheduled = date.today() + timedelta(days=days_ahead)
    while scheduled.weekday() >= 5:
        scheduled += timedelta(days=1)
    return scheduled


def _seed_user(name, email, password, role):
    found = next((user for user in data_access.get_all_records("user")
                  if user.get("email", "").casefold() == email.casefold()), None)
    if found:
        return found
    user, status = create_user({
        "name": name, "email": email, "password": password, "role": role,
    })
    if status != 201:
        raise RuntimeError(user.get("error", f"Could not create {email}"))
    return user


def main():
    _seed_user("Demo Admin", "admin@salises.test", "AdminPass123", "admin")
    _seed_user("Demo Staff", "staff@salises.test", "StaffPass123", "staff")

    visitors = [
        _get_or_create("visitor", "student_id", "DEMO-UG-001", {
            "student_id": "DEMO-UG-001", "name": "Maya Brown",
            "phone_number": "876-555-0101", "type": "undergraduate",
            "faculty": "Social Sciences", "purpose": "Research",
        }),
        _get_or_create("visitor", "student_id", "DEMO-PG-001", {
            "student_id": "DEMO-PG-001", "name": "Daniel King",
            "phone_number": "876-555-0102", "type": "postgraduate",
            "faculty": "Humanities", "purpose": "Consultation",
        }),
        _get_or_create("visitor", "name", "Leah Grant", {
            "student_id": None, "name": "Leah Grant",
            "phone_number": "876-555-0103", "type": "external",
            "faculty": None, "purpose": "Seminar",
        }),
    ]

    books = [
        _get_or_create("book", "name", "Demo: Caribbean Economic Survey", {
            "name": "Demo: Caribbean Economic Survey", "author": "SALISES",
            "price": 4500.0, "genre": "Economics", "status": "reserved",
            "condition": "good",
        }),
        _get_or_create("book", "name", "Demo: Statistical Digest", {
            "name": "Demo: Statistical Digest", "author": "SALISES",
            "price": 3200.0, "genre": "Research", "status": "available",
            "condition": "good",
        }),
    ]
    journal = _get_or_create("journal", "name", "Demo: Caribbean Dialogue", {
        "name": "Demo: Caribbean Dialogue", "author": "SALISES",
        "price": 2500.0, "stock": 12, "status": "available", "condition": "good",
    })
    room = _get_or_create("room", "name", "Demo: Seminar Room", {
        "name": "Demo: Seminar Room", "capacity": 20,
        "status": "available", "condition": "good",
    })
    archival = _get_or_create("archival", "name", "Demo: Historical Map Collection", {
        "name": "Demo: Historical Map Collection", "status": "available",
        "condition": "good",
    })

    today = date.today()
    future_date = _next_weekday(7).isoformat()
    reservations = [
        (visitors[0], room, "room", "pending"),
        (visitors[1], archival, "archival", "declined"),
        (visitors[0], books[0], "book", "approved"),
    ]
    for index, (visitor, resource, resource_type, status) in enumerate(reservations):
        identity = f"demo-reservation-{index + 1}"
        _get_or_create("reservation", "demo_key", identity, {
            "demo_key": identity,
            "visitor_id": visitor["id"], "resource_id": resource["id"],
            "reservation_type": resource_type, "status": status,
            "request_date": today.isoformat(),
            **({"reserve_date": future_date, "start_time": "10:00", "end_time": "11:00",
                **({"occupants": 8} if resource_type == "room" else {})}
               if resource_type in {"room", "archival"} else {
                   "expected_return": (today + timedelta(days=14)).isoformat(),
                   "actual_return": None,
               }),
        })

    for index, visitor in enumerate(visitors):
        identity = f"demo-visit-{index + 1}"
        _get_or_create("visit", "demo_key", identity, {
            "demo_key": identity, "visitor_id": visitor["id"],
            "purpose": visitor["purpose"],
            "check_in": (today - timedelta(days=index)).isoformat() + "T09:00:00+00:00",
            "check_out": None if index == 0 else (today - timedelta(days=index)).isoformat() + "T10:00:00+00:00",
        })

    _get_or_create("sale", "demo_key", "demo-sale-1", {
        "demo_key": "demo-sale-1", "journal_id": journal["id"],
        "quantity": 2, "sale_amount": 5000.0,
        "date_sold": today.isoformat(), "payment_confirmed": False,
    })
    _get_or_create("fine", "demo_key", "demo-fine-unpaid", {
        "demo_key": "demo-fine-unpaid", "visitor_id": visitors[0]["id"],
        "resource_id": books[0]["id"], "reason": "late", "amount": 150.0,
        "date_issued": today.isoformat(), "status": "unpaid",
    })
    _get_or_create("fine", "demo_key", "demo-fine-paid", {
        "demo_key": "demo-fine-paid", "visitor_id": visitors[1]["id"],
        "resource_id": books[1]["id"], "reason": "damaged", "amount": 300.0,
        "date_issued": today.isoformat(), "status": "paid",
    })

    print("Demo data is ready in ./data")
    print("Admin: admin@salises.test / AdminPass123")
    print("Staff: staff@salises.test / StaffPass123")
    print("Visitor IDs:", ", ".join(str(item["id"]) for item in visitors))


if __name__ == "__main__":
    main()
