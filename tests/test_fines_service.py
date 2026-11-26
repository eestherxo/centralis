from datetime import date

import pytest

from app import data_access
from app.modules import resource_fines


@pytest.fixture(autouse=True)
def temp_data(tmp_path, monkeypatch):
    # Use a temporary folder so tests never touch the real data files
    monkeypatch.setattr(data_access, "DB_DIR", tmp_path)
    # Fix "today" so late fines can be checked exactly
    monkeypatch.setattr(resource_fines, "_today", lambda: date(2026, 11, 21))


def make_user(role):
    user = data_access.create(
        "user", {"name": f"Test {role}", "email": f"{role}@test.com", "password": "x", "role": role}
    )
    return user["id"]


@pytest.fixture
def staff():
    return make_user("staff")


@pytest.fixture
def admin():
    return make_user("admin")


@pytest.fixture
def outsider():
    # A logged-in user who is not SALISES staff
    return make_user("guest")


@pytest.fixture
def visitor():
    return data_access.create(
        "visitor",
        {"name": "Ashleigh Brown", "phone_number": "876-555-0101",
         "type": "postgraduate", "purpose": "Research"},
    )


def make_book(name="Caribbean Economic Survey", price=4500.0, **changes):
    book = {"name": name, "author": "SALISES", "price": price, "genre": "Economics",
            "status": "reserved", "condition": "good"}
    book.update(changes)
    return data_access.create("book", book)


def make_loan(visitor, book, expected_return="2026-11-14"):
    # An approved book loan, as the reservation feature saves it
    return data_access.create(
        "reservation",
        {"visitor_id": visitor["id"], "resource_id": book["id"],
         "reservation_type": "book", "status": "approved",
         "request_date": "2026-11-07", "expected_return": expected_return,
         "actual_return": None},
    )


@pytest.fixture
def book():
    return make_book()


@pytest.fixture
def loan(visitor, book):
    return make_loan(visitor, book)


# late returns and fines

def test_late_return_fine_calculated(staff, loan, visitor, book):
    # This test if the fine is calculated correctly for a late return (7 days late)
    result = resource_fines.record_return(staff, loan["id"], "2026-11-17")

    assert len(result["fines"]) == 1
    fine = result["fines"][0]
    assert fine["amount"] == 150.0
    assert fine["reason"] == "late"
    assert fine["status"] == "unpaid"
    assert fine["visitor_id"] == visitor["id"]
    assert fine["resource_id"] == book["id"]
    assert fine["date_issued"] == "2026-11-21"


def test_fine_record_keeps_every_required_field(staff, loan):
    fine = resource_fines.record_return(staff, loan["id"], "2026-11-17")["fines"][0]

    for field in ("id", "visitor_id", "resource_id", "reason", "amount", "date_issued", "status"):
        assert field in fine
    assert fine.get("date_paid") is None  # only filled in when the fine is paid


def test_return_on_time_has_no_fine_and_book_is_available(staff, loan, book):
    result = resource_fines.record_return(staff, loan["id"], "2026-11-13")

    assert result["fines"] == []
    assert data_access.get_all_records("fine") == []
    saved = data_access.get_record("book", book["id"])
    assert saved["status"] == "available"
    assert saved["condition"] == "good"
    assert result["reservation"]["actual_return"] == "2026-11-13"


def test_return_on_the_due_date_is_not_late(staff, loan):
    assert resource_fines.record_return(staff, loan["id"], "2026-11-14")["fines"] == []


def test_return_date_defaults_to_today(staff, loan):
    #  For this test, the date is set to 2026-11-21 so the loan is 7 days late
    fine = resource_fines.record_return(staff, loan["id"])["fines"][0]

    assert fine["amount"] == 350.0


@pytest.mark.parametrize(
    "expected, actual, days, amount",
    [
        (date(2026, 11, 14), date(2026, 11, 14), 0, 0.0),
        (date(2026, 11, 14), date(2026, 11, 15), 1, 50.0),
        (date(2026, 11, 14), date(2026, 11, 10), 0, 0.0),
        (date(2026, 11, 14), date(2026, 12, 14), 30, 1500.0),
    ],
)
def test_calculate_late_fine(expected, actual, days, amount):
    assert resource_fines.calculate_late_fine(expected, actual) == (days, amount)
    assert resource_fines.calculate_fine(expected, actual) == amount


def test_loan_cannot_be_returned_twice(staff, loan):
    resource_fines.record_return(staff, loan["id"], "2026-11-17")

    with pytest.raises(ValueError):
        resource_fines.record_return(staff, loan["id"], "2026-11-18")

    assert len(data_access.get_all_records("fine")) == 1


def test_invalid_return_date_saves_nothing(staff, loan):
    with pytest.raises(ValueError):
        resource_fines.record_return(staff, loan["id"], "17/11/2026")

    assert data_access.get_all_records("fine") == []
    assert data_access.get_record("reservation", loan["id"])["actual_return"] is None


def test_unknown_loan_not_found(staff):
    with pytest.raises(resource_fines.FineNotFound):
        resource_fines.record_return(staff, 69699999, "2026-11-17")


def test_non_book_reservation_cannot_be_returned(staff, visitor):
    room = data_access.create(
        "room", {"name": "Seminar Room", "capacity": 20, "status": "available", "condition": "good"}
    )
    reservation = data_access.create(
        "reservation",
        {"visitor_id": visitor["id"], "resource_id": room["id"],
         "reservation_type": "room", "status": "approved"},
    )

    with pytest.raises(ValueError):
        resource_fines.record_return(staff, reservation["id"], "2026-11-17")


def test_returned_damaged_and_late_gets_both_fines(staff, loan, book):
    result = resource_fines.record_return(staff, loan["id"], "2026-11-16", condition="damaged")

    assert [(f["reason"], f["amount"]) for f in result["fines"]] == [
        ("late", 100.0), ("damaged", 4500.0)]
    assert len({f["id"] for f in result["fines"]}) == 2
    assert data_access.get_record("book", book["id"])["condition"] == "damaged"


def test_damaged_return_without_price_saves_nothing(staff, visitor):
    book = make_book(price=0)
    loan = make_loan(visitor, book)

    with pytest.raises(ValueError):
        resource_fines.record_return(staff, loan["id"], "2026-11-17", condition="damaged")

    assert data_access.get_all_records("fine") == []
    assert data_access.get_record("reservation", loan["id"])["actual_return"] is None


# lost and damaged resources

def test_fine_recorded_for_lost_resource(staff, loan, visitor, book):
    fine = resource_fines.lost_or_damaged(staff, book["id"], "lost")

    assert fine["reason"] == "lost"
    assert fine["amount"] == 4500.0
    assert fine["status"] == "unpaid"
    assert fine["visitor_id"] == visitor["id"]  # the borrower on the active loan
    assert data_access.get_record("book", book["id"])["condition"] == "lost"
    assert resource_fines.active_loans(staff) == []  # the loan is finished once the book is lost


def test_fine_recorded_for_damaged_resource(admin, loan, book):
    fine = resource_fines.lost_or_damaged(admin, book["id"], "damaged")

    assert (fine["reason"], fine["amount"]) == ("damaged", 4500.0)
    assert data_access.get_record("book", book["id"])["condition"] == "damaged"


def test_staff_can_name_the_responsible_borrower(staff, visitor):
    book = make_book(status="available")

    fine = resource_fines.lost_or_damaged(staff, book["id"], "lost", visitor["id"])

    assert fine["visitor_id"] == visitor["id"]


def test_borrower_needed_when_there_is_no_active_loan(staff):
    book = make_book(status="available")

    with pytest.raises(ValueError):
        resource_fines.lost_or_damaged(staff, book["id"], "lost")

    assert data_access.get_record("book", book["id"])["condition"] == "good"


def test_unknown_borrower_not_found(staff):
    book = make_book(status="available")

    with pytest.raises(resource_fines.FineNotFound):
        resource_fines.lost_or_damaged(staff, book["id"], "lost", 19100001)

    assert data_access.get_all_records("fine") == []


def test_resource_without_price_rejected_and_unchanged(staff, visitor):
    item = data_access.create(
        "archival", {"name": "Tape Recording", "status": "available", "condition": "good"}
    )

    with pytest.raises(ValueError):
        resource_fines.lost_or_damaged(staff, item["id"], "damaged", visitor["id"])

    assert data_access.get_all_records("fine") == []
    assert data_access.get_record("archival", item["id"])["condition"] == "good"


def test_same_resource_cannot_be_fined_twice(staff, loan, book):
    resource_fines.lost_or_damaged(staff, book["id"], "lost")

    with pytest.raises(ValueError):
        resource_fines.lost_or_damaged(staff, book["id"], "damaged")

    assert len(data_access.get_all_records("fine")) == 1


def test_only_lost_or_damaged_accepted(staff, book):
    with pytest.raises(ValueError):
        resource_fines.lost_or_damaged(staff, book["id"], "good")


def test_unknown_resource_not_found(staff):
    with pytest.raises(resource_fines.FineNotFound):
        resource_fines.lost_or_damaged(staff, 29299999, "lost")


# ---------- viewing ----------

def test_staff_view_a_borrowers_unpaid_fines(staff, loan, visitor):
    resource_fines.record_return(staff, loan["id"], "2026-11-17", condition="damaged")

    fines = resource_fines.unpaid_fines(staff, visitor["id"])

    assert [(f["reason"], f["amount"]) for f in fines] == [("late", 150.0), ("damaged", 4500.0)]
    assert fines[0]["resource_name"] == "Caribbean Economic Survey"
    assert fines[0]["visitor_name"] == "Ashleigh Brown"
    assert fines[0]["date_issued"] == "2026-11-21"


def test_paid_fines_are_not_listed_as_unpaid(staff, loan, visitor):
    fine = resource_fines.record_return(staff, loan["id"], "2026-11-17")["fines"][0]
    resource_fines.confirm_payment(staff, fine["id"])

    assert resource_fines.unpaid_fines(staff, visitor["id"]) == []


def test_other_visitors_fines_are_not_listed(staff, loan):
    resource_fines.record_return(staff, loan["id"], "2026-11-17")
    other = data_access.create(
        "visitor",
        {"name": "Marcus Reid", "phone_number": "876-555-0102",
         "type": "external", "purpose": "Research"},
    )

    assert resource_fines.unpaid_fines(staff, other["id"]) == []


def test_unpaid_fines_for_unknown_visitor(staff):
    with pytest.raises(resource_fines.FineNotFound):
        resource_fines.unpaid_fines(staff, 19100099)


def test_list_fines_can_filter_by_status(staff, loan):
    resource_fines.record_return(staff, loan["id"], "2026-11-17", condition="damaged")
    first = data_access.get_all_records("fine")[0]
    resource_fines.confirm_payment(staff, first["id"])

    assert len(resource_fines.list_fines(staff)) == 2
    assert [f["status"] for f in resource_fines.list_fines(staff, "unpaid")] == ["unpaid"]
    assert [f["status"] for f in resource_fines.list_fines(staff, "paid")] == ["paid"]
    with pytest.raises(ValueError):
        resource_fines.list_fines(staff, "overdue")


def test_active_loans_show_how_late_each_one_is(staff, visitor):
    late = make_loan(visitor, make_book("Late Book"), "2026-11-14")
    on_time = make_loan(visitor, make_book("On Time Book"), "2026-12-05")

    rows = {row["id"]: row for row in resource_fines.active_loans(staff)}

    assert rows[late["id"]]["days_late"] == 7
    assert rows[late["id"]]["fine_so_far"] == 350.0
    assert rows[late["id"]]["resource_name"] == "Late Book"
    assert rows[on_time["id"]]["fine_so_far"] == 0.0


def test_return_only_adds_the_actual_return_date_to_the_loan(staff, loan):
    before = data_access.get_record("reservation", loan["id"])

    resource_fines.record_return(staff, loan["id"], "2026-11-17")

    after = data_access.get_record("reservation", loan["id"])
    assert after.keys() == before.keys()  # no new fields added to the loan record
    assert {k for k in after if after[k] != before[k]} == {"actual_return"}


def test_marking_lost_does_not_change_the_loan_record(staff, loan, book):
    before = data_access.get_record("reservation", loan["id"])

    resource_fines.lost_or_damaged(staff, book["id"], "lost")

    assert data_access.get_record("reservation", loan["id"]) == before


def test_returned_loans_are_not_listed_as_active(staff, loan):
    resource_fines.record_return(staff, loan["id"], "2026-11-17")

    assert resource_fines.active_loans(staff) == []


def test_visitor_and_resource_pickers(staff, visitor, book):
    make_book("No Price", price=0)
    make_book("Already Lost", condition="lost")

    visitors = resource_fines.list_visitors(staff)
    resources = resource_fines.resources_condition(staff)

    assert [v["name"] for v in visitors] == ["Ashleigh Brown"]
    assert [r["name"] for r in resources] == ["Caribbean Economic Survey"]


# payments and receipts

@pytest.fixture
def fine(staff, loan):
    return resource_fines.record_return(staff, loan["id"], "2026-11-17")["fines"][0]


def test_fine_marked_as_paid(staff, fine):
    paid = resource_fines.confirm_payment(staff, fine["id"])

    assert paid["status"] == "paid"
    assert paid["date_paid"] == "2026-11-21"


def test_fine_cannot_be_paid_twice(staff, fine):
    resource_fines.confirm_payment(staff, fine["id"])

    with pytest.raises(ValueError):
        resource_fines.confirm_payment(staff, fine["id"])


def test_unknown_fine_not_found(staff):
    with pytest.raises(resource_fines.FineNotFound):
        resource_fines.confirm_payment(staff, 79799999)


def test_receipt_has_the_required_details(staff, fine):
    resource_fines.confirm_payment(staff, fine["id"])

    receipt = resource_fines.generate_receipt(staff, fine["id"])

    assert receipt == {
        "receipt_number": fine["id"],
        "visitor_name": "Ashleigh Brown",
        "resource_name": "Caribbean Economic Survey",
        "fine_type": "late",
        "amount_paid": 150.0,
        "payment_date": "2026-11-21",
    }


def test_no_receipt_for_unpaid_fine(staff, fine):
    with pytest.raises(resource_fines.PaymentNotConfirmed):
        resource_fines.generate_receipt(staff, fine["id"])

    with pytest.raises(resource_fines.PaymentNotConfirmed):
        resource_fines.generate_receipt_pdf(staff, fine["id"])


def test_receipt_pdf_is_generated_after_payment(staff, fine):
    resource_fines.confirm_payment(staff, fine["id"])

    pdf = resource_fines.generate_receipt_pdf(staff, fine["id"]).read()

    assert pdf.startswith(b"%PDF")
    assert b"Ashleigh Brown" in pdf
    assert b"Caribbean Economic Survey" in pdf
    assert b"$150.00" in pdf
    assert b"2026-11-21" in pdf


# Authorisation checks 

@pytest.mark.parametrize("who", ["outsider", "nobody", "missing"])
def test_unauthorized_user_cannot_change_fines(who, request, staff, loan, book, visitor, fine):
    logged_in_user = {"outsider": lambda: request.getfixturevalue("outsider"),
             "nobody": lambda: None,
             "missing": lambda: 99999999}[who]()
    before = (data_access.get_all_records("fine"), data_access.get_all_records("reservation"),
              data_access.get_all_records("book"))

    actions = (
        lambda: resource_fines.record_return(logged_in_user, loan["id"], "2026-11-17"),
        lambda: resource_fines.lost_or_damaged(logged_in_user, book["id"], "lost"),
        lambda: resource_fines.confirm_payment(logged_in_user, fine["id"]),
        lambda: resource_fines.generate_receipt(logged_in_user, fine["id"]),
        lambda: resource_fines.unpaid_fines(logged_in_user, visitor["id"]),
        lambda: resource_fines.list_fines(logged_in_user),
        lambda: resource_fines.active_loans(logged_in_user),
        lambda: resource_fines.list_visitors(logged_in_user),
        lambda: resource_fines.resources_condition(logged_in_user),
    )
    for action in actions:
        with pytest.raises(resource_fines.PermissionDenied):
            action()

    after = (data_access.get_all_records("fine"), data_access.get_all_records("reservation"),
             data_access.get_all_records("book"))
    assert before == after


def test_admin_counts_as_authorized_staff(admin, loan):
    assert resource_fines.record_return(admin, loan["id"], "2026-11-13")["fines"] == []
