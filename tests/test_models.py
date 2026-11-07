from app.models import ArchivalItem, Book, Journal, ResourceCategory, Room


def test_book_model():
    book = Book(
        id=1,
        name="Dune",
        author="Frank Herbert",
        collection="Science Fiction",
        price=12.99,
    )

    assert book.to_dict() == {
        "id": 1,
        "name": "Dune",
        "status": "available",
        "category": "book",
        "author": "Frank Herbert",
        "collection": "Science Fiction",
        "price": 12.99,
    }


def test_archival_item_model():
    item = ArchivalItem(
        id=2,
        name="Old map",
        author="Unknown",
        collection="Maps",
    )

    data = item.to_dict()
    assert data["category"] == ResourceCategory.ARCHIVAL.value
    assert "price" not in item.to_dict()


def test_journal_model():
    journal = Journal(
        id=3,
        name="Research Monthly",
        author="Various",
        collection="Science",
        price=8.50,
        issue="Vol. 2",
        stock=10,
    )

    data = journal.to_dict()
    assert data["category"] == ResourceCategory.JOURNAL.value
    assert data["price"] == 8.50
    assert data["issue"] == "Vol. 2"
    assert data["stock"] == 10


def test_room_model():
    room = Room(id=4, name="Study room", capacity=6)

    data = room.to_dict()
    assert data["capacity"] == 6
