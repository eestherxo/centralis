"""Adds demo data so the fines endpoints can be tried by hand.

Run from the project folder:   python -m scripts.seed_fines_demo

It creates (in ./data, which git ignores):
  - a staff account   staff@salises.test / StaffPass123
  - an admin account  admin@salises.test / AdminPass123
  - 2 visitors, 4 books and 3 approved book loans (one is 7 days late)
Running it twice does nothing the second time.
"""
from datetime import date, timedelta

from app import data_access
from app.modules.authentication import create_user


def main():
    if any(u["email"] == "staff@salises.test" for u in data_access.get_all_records("user")):
        print("Demo data already exists. Delete the ./data folder to start again.")
        return

    for name, email, password, role in (
        ("Demo Staff", "staff@salises.test", "StaffPass123", "staff"),
        ("Demo Admin", "admin@salises.test", "AdminPass123", "admin"),
    ):
        user, status = create_user(
            {"name": name, "email": email, "password": password, "role": role}
        )
        print(f"user {email}: {status}")

    visitors = [
        data_access.create("visitor", {"name": "Ashleigh Brown", "phone_number": "876-555-0101",
                                       "type": "postgraduate", "purpose": "Research"}),
        data_access.create("visitor", {"name": "Marcus Reid", "phone_number": "876-555-0102",
                                       "type": "external", "purpose": "Research"}),
    ]

    books = [
        data_access.create("book", {"name": title, "author": "SALISES", "price": price,
                                    "genre": "Economics", "status": "reserved", "condition": "good"})
        for title, price in (
            ("Caribbean Economic Survey", 4500.0),
            ("Working Paper Series Vol. 12", 6200.0),
            ("Statistical Digest of Jamaica", 3800.0),
        )
    ]
    data_access.create("book", {"name": "Spare Copy", "author": "SALISES", "price": 3000.0,
                                "genre": "Economics", "status": "available", "condition": "good"})

    today = date.today()
    # (borrower, book, days until the book is due; negative means already late)
    for visitor, book, due_in in ((visitors[0], books[0], -7), (visitors[1], books[1], 14),
                                  (visitors[0], books[2], 0)):
        data_access.create("reservation", {
            "visitor_id": visitor["id"], "resource_id": book["id"],
            "reservation_type": "book", "status": "approved",
            "request_date": (today - timedelta(days=21)).isoformat(),
            "expected_return": (today + timedelta(days=due_in)).isoformat(),
            "actual_return": None,
        })

    print("Demo data created.")
    for v in visitors:
        print("visitor", v["id"], v["name"])
    for b in books:
        print("book   ", b["id"], b["name"])


if __name__ == "__main__":
    main()
