from datetime import date, time

from app.models import (
    Visitor,
    ArchivalItem,
    ArchivalReservation,
    Book,
    BookReservation,
    Fine,
    FineReason,
    FineStatus,
    Journal,
    ReservationStatus,
    ResourceCondition,
    ResourceStatus,
    ResourceType,
    Room,
    RoomReservation,
    Sale,
)


from app.models import Visitor, VisitorType


def test_undergraduate_visitor_model():
    visitor = Visitor(
        "Taylor Smith",
        "555-0123",
        VisitorType.UNDERGRAD,
        "library research",
        student_id=123456,
        faculty="Science",
    )
    data = visitor.to_dict()
    print(f"\n{data}\n")

    assert visitor.type is VisitorType.UNDERGRAD
    assert visitor.student_id == 123456
    assert visitor.faculty == "Science"


def test_external_visitor_model():
    visitor = Visitor(
        "Morgan Brown",
        "555-0456",
        VisitorType.EXTERNAL,
        "attend a seminar",
    )
    data = visitor.to_dict()
    print(f"{data}\n")

    assert visitor.type is VisitorType.EXTERNAL
    assert visitor.student_id is None
    assert visitor.faculty is None

def test_book_model():
    book = Book(
        name="Animal Farm",
        author="George Orwell",
        price=6465,
        genre="Dystopian",
    )

    data = book.to_dict()
    print(f"{data}\n")

    assert book.id is None
    assert book.status is ResourceStatus.AVAILABLE
    assert book.condition is ResourceCondition.GOOD
    assert data == {
        "id": None,
        "name": "Animal Farm",
        "resource_type": ResourceType.BOOK.value,
        "status": ResourceStatus.AVAILABLE.value,
        "condition": ResourceCondition.GOOD.value,
        "author": "George Orwell",
        "price": 6465,
        "genre": "Dystopian",
    }


def test_journal_model():
    journal = Journal(
        name="Research Monthly",
        author="Various",
        price=8.50,
        stock=10,
    )

    data = journal.to_dict()
    print(f"{data}\n")

    assert journal.id is None
    assert journal.status is ResourceStatus.AVAILABLE
    assert journal.condition is ResourceCondition.GOOD
    assert data == {
        "id": None,
        "name": "Research Monthly",
        "resource_type": ResourceType.JOURNAL.value,
        "status": ResourceStatus.AVAILABLE.value,
        "condition": ResourceCondition.GOOD.value,
        "author": "Various",
        "price": 8.50,
        "stock": 10,
    }


def test_archival_item_model():
    item = ArchivalItem(name="Old map")

    data = item.to_dict()
    print(f"{data}\n")

    assert item.id is None
    assert item.status is ResourceStatus.AVAILABLE
    assert item.condition is ResourceCondition.GOOD
    assert data == {
        "id": None,
        "name": "Old map",
        "resource_type": ResourceType.ARCHIVAL.value,
        "status": ResourceStatus.AVAILABLE.value,
        "condition": ResourceCondition.GOOD.value,
    }


def test_room_model():
    room = Room(name="Study room", capacity=6)

    data = room.to_dict()
    print(f"{data}\n")

    assert room.id is None
    assert room.status is ResourceStatus.AVAILABLE
    assert room.condition is ResourceCondition.GOOD
    assert data == {
        "id": None,
        "name": "Study room",
        "resource_type": ResourceType.ROOM.value,
        "status": ResourceStatus.AVAILABLE.value,
        "condition": ResourceCondition.GOOD.value,
        "capacity": 6,
    }


def test_room_reservation_model():
    reservation = RoomReservation(
        visitor=20,
        resource=4,
        request_date=date(2026, 11, 1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        reserve_date=date(2026, 11, 20),
        occupants=5,
    )

    data = reservation.to_dict()
    print(f"{data}\n")

    assert reservation.status is ReservationStatus.PENDING
    assert data["visitor_id"] == 20
    assert data["resource_id"] == 4
    assert data["reservation_type"] == ResourceType.ROOM.value
    assert data["status"] == ReservationStatus.PENDING.value
    assert data["request_date"] == date(2026, 11, 1)
    assert data["occupants"] == 5


def test_archival_reservation_model():
    reservation = ArchivalReservation(
        visitor=21,
        resource=2,
        request_date=date(2026, 11, 1),
        start_time=time(13, 0),
        end_time=time(14, 0),
        reserve_date=date(2026, 11, 22),
    )

    data = reservation.to_dict()
    print(f"{data}\n")

    assert reservation.status is ReservationStatus.PENDING
    assert data["visitor_id"] == 21
    assert data["resource_id"] == 2
    assert data["reservation_type"] == ResourceType.ARCHIVAL.value
    assert data["status"] == ReservationStatus.PENDING.value


def test_book_reservation_model():
    reservation = BookReservation(
        visitor=22,
        resource=1,
        request_date=date(2026, 11, 1),
        start_time=time(9, 0),
        end_time=time(9, 15),
        reserve_date=date(2026, 11, 21),
        expected_return=date(2026, 12, 5),
        actual_return=date(2026, 12, 4),
    )

    data = reservation.to_dict()
    print(f"{data}\n")

    assert reservation.status is ReservationStatus.PENDING
    assert data["reservation_type"] == ResourceType.BOOK.value
    assert data["expected_return"] == date(2026, 12, 5)
    assert data["actual_return"] == date(2026, 12, 4)


def test_fine_model():
    fine = Fine(
        visitor=22,
        resource=1,
        reason=FineReason.LATE,
        amount=5.0,
        date_issued=date(2026, 12, 6),
    )

    data = fine.to_dict()
    print(f"{data}\n")

    assert fine.status is FineStatus.UNPAID
    assert data["visitor_id"] == 22
    assert data["resource_id"] == 1
    assert data["reason"] is FineReason.LATE
    assert data["amount"] == 5.0
    assert data["date_issued"] == date(2026, 12, 6)


def test_sale_model():
    sale = Sale(
        journal=3,
        quantity=2,
        sale_amount=17.0,
        date_sold=date(2026, 11, 18),
    )

    data = sale.to_dict()
    print(f"{data}")

    assert data == {
        "id": None,
        "journal_id": 3,
        "quantity": 2,
        "sale_amount": 17.0,
        "date_sold": date(2026, 11, 18),
        "payment_confirmed": False,
    }
