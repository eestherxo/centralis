from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import ClassVar
from datetime import date, time 


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"


class ResourceType(str, Enum):
    BOOK = "book"
    ARCHIVAL = "archival"
    JOURNAL = "journal"
    ROOM = "room"


class ResourceCondition(str, Enum):
    GOOD = "good"
    LOST = "lost"
    DAMAGED = "damaged"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"



class FineStatus(str, Enum):
    PAID = "paid"
    UNPAID = "unpaid"


class FineReason(str, Enum):
    LATE = "late"
    LOST = "lost"
    DAMAGED = "damaged"

class VisitorType(str, Enum):
    UNDERGRAD = "undergraduate"
    POSTGRAD = "postgraduate"
    EXTERNAL = "external"


@dataclass
class Visitor:
    id: int | None = field(default=None, kw_only=True)
    student_id: int | None = field(default=None, kw_only=True)
    id_number: str | None = field(default=None, kw_only=True)
    name: str 
    phone_number: str
    type: VisitorType
    faculty: str | None = field(default=None, kw_only=True)
    purpose: str

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "id_number": self.id_number,
            "name": self.name,
            "phone_number": self.phone_number,
            "type": self.type.value,
            "faculty": self.faculty,
            "purpose": self.purpose
        }


@dataclass
class Resource(ABC):
    id: int | None = field(default=None, kw_only=True)
    name: str
    type: ClassVar[ResourceType] # static attribute
    status: ResourceStatus = field(default=ResourceStatus.AVAILABLE, kw_only=True) 
    condition: ResourceCondition = field(default=ResourceCondition.GOOD, kw_only=True)

    @abstractmethod
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "resource_type": self.type.value,
            "status": self.status.value,
            "condition": self.condition.value,
        }


@dataclass
class Publication(Resource):
    author: str
    price: float


@dataclass
class Book(Publication):
    type: ClassVar[ResourceType] = ResourceType.BOOK
    genre: str 

    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "author": self.author,
                "price": self.price,
                "genre": self.genre,
            }
        )
        return object


@dataclass
class Journal(Publication):
    type: ClassVar[ResourceType] = ResourceType.JOURNAL
    stock: int

    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "author": self.author,
                "price": self.price,
                "stock": self.stock,
            }
        )
        return object


@dataclass
class ArchivalItem(Resource):
    type: ClassVar[ResourceType] = ResourceType.ARCHIVAL

    def to_dict(self) -> dict:
        object = super().to_dict()
        return object


@dataclass
class Room(Resource):
    type: ClassVar[ResourceType] = ResourceType.ROOM
    capacity: int
    
    def to_dict(self) -> dict:
        object = super().to_dict()
        object.update(
            {
                "capacity": self.capacity,
            }
        )
        return object


@dataclass
class Reservation(ABC):
    id: int | None = field(default=None, kw_only=True)
    visitor: int 
    resource: int 
    type: ClassVar[ResourceType] # static attribute
    status: ReservationStatus = field(default=ReservationStatus.PENDING, kw_only=True)
    request_date: date 

    @abstractmethod
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "visitor_id": self.visitor,
            "resource_id": self.resource,
            "reservation_type": self.type.value, 
            "status": self.status.value,
            "request_date": self.request_date
        }


@dataclass
class OnsitReservation(Reservation):
    start_time: time
    end_time: time
    reserve_date: date 


@dataclass
class RoomReservation(OnsitReservation):
    type: ClassVar[ResourceType] = ResourceType.ROOM
    occupants: int 

    def to_dict(self):
        object = super().to_dict()
        object.update(
            {
                "occupants": self.occupants
            }
        )
        return object

    
@dataclass
class ArchivalReservation(OnsitReservation):
    type: ClassVar[ResourceType] = ResourceType.ARCHIVAL

    def to_dict(self):
        object = super().to_dict()
        return object

    
@dataclass
class BookReservation(OnsitReservation):
    type: ClassVar[ResourceType] = ResourceType.BOOK
    expected_return: date  
    actual_return: date 

    def to_dict(self):
        object = super().to_dict()
        object.update(
            {
                "expected_return": self.expected_return,
                "actual_return": self.actual_return
            }
        )
        return object


@dataclass
class Fine:
    id: int | None = field(default=None, kw_only=True)
    visitor: int 
    resource: int 
    reason: FineReason
    amount: float
    date_issued: date
    status: FineStatus = field(default=FineStatus.UNPAID, kw_only=True)

    def to_dict(self):
        return {
            "id": self.id,
            "visitor_id": self.visitor,
            "resource_id": self.resource,
            "reason": self.reason,
            "amount": self.amount,
            "date_issued": self.date_issued,
            "status": self.status
        }


@dataclass
class Sale:
    id: int | None = field(default=None, kw_only=True)
    journal: int 
    quantity: int 
    sale_amount: float 
    date_sold: date 

    def to_dict(self):
        return {
            "id": self.id,
            "journal_id": self.journal,
            "quantity": self.quantity,
            "sale_amount": self.sale_amount,
            "date_sold": self.date_sold,
            }