from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import ClassVar


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    LOST = "lost"
    DAMAGED = "damaged"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class ResourceCategory(str, Enum):
    BOOK = "book"
    ARCHIVAL = "archival"
    JOURNAL = "journal"
    ROOM = "room"


@dataclass
class Resource(ABC):
    id: int | None = field(default=None, kw_only=True)
    name: str
    status: ResourceStatus = field(default=ResourceStatus.AVAILABLE, kw_only=True)
    category: ClassVar[ResourceCategory]

    @abstractmethod
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "category": self.category.value,
        }


@dataclass
class Room(Resource):
    capacity: int
    category: ClassVar[ResourceCategory] = ResourceCategory.ROOM

    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "capacity": self.capacity,
            }
        )
        return object


@dataclass
class Publication(Resource):
    author: str
    collection: str


@dataclass
class Book(Publication):
    price: float
    category: ClassVar[ResourceCategory] = ResourceCategory.BOOK

    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "author": self.author,
                "collection": self.collection,
                "price": self.price,
            }
        )
        return object


@dataclass
class ArchivalItem(Publication):
    category: ClassVar[ResourceCategory] = ResourceCategory.ARCHIVAL

    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "author": self.author,
                "collection": self.collection,
            }
        )
        return object


@dataclass
class Journal(Publication):
    price: float
    issue: str
    category: ClassVar[ResourceCategory] = ResourceCategory.JOURNAL
    stock: int

    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "author": self.author,
                "collection": self.collection,
                "price": self.price,
                "issue": self.issue,
                "stock": self.stock,
            }
        )
        return object
