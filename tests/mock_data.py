"""Small records matching the JSON schema stored by Centralis services."""

MOCK_REPORT_DATA = {
    "visitor": [
        {"visitor_id": 19100001, "name": "Maya Brown", "type": "undergraduate", "check_in": "2026-11-01T09:00:00+00:00"},
        {"visitor_id": 19100001, "name": "Maya Brown", "type": "undergraduate", "check_in": "2026-11-08T09:00:00+00:00"},
        {"visitor_id": 19100002, "name": "Daniel King", "type": "postgraduate", "check_in": "2026-11-15T09:00:00+00:00"},
        {"visitor_id": 19100003, "name": "Leah Grant", "type": "external", "check_in": "2026-11-30T09:00:00+00:00"},
        {"visitor_id": 19100004, "name": "Owen Clarke", "type": "external", "check_in": "2026-12-01T09:00:00+00:00"},
    ],
    "reservation": [
        {"id": 69600001, "visitor_id": 19100001, "resource_id": 39300001,
         "reservation_type": "room", "request_date": "2026-11-10", "status": "approved"},
        {"id": 69600002, "visitor_id": 19100002, "resource_id": 59500001,
         "reservation_type": "archival", "request_date": "2026-11-18", "status": "pending"},
        {"id": 69600003, "visitor_id": 19100003, "resource_id": 39300002,
         "reservation_type": "room", "request_date": "2026-12-02", "status": "declined"},
    ],
    "journal_sales": [
        {"id": 89800001, "journal_id": 49400001, "quantity": 2,
         "date_sold": "2026-11-12", "sale_amount": 5000.0, "payment_confirmed": False},
        {"id": 89800002, "journal_id": 49400002, "quantity": 1,
         "date_sold": "2026-11-20", "sale_amount": 2500.0, "payment_confirmed": True},
        {"id": 89800003, "journal_id": 49400001, "quantity": 1,
         "date_sold": "2026-10-31", "sale_amount": 2500.0, "payment_confirmed": True},
    ],
    "fines": [
        {"id": 79700001, "visitor_id": 19100001, "reason": "late", "amount": 150.0,
         "resource_id": 29200001, "date_issued": "2026-11-15", "status": "unpaid"},
        {"id": 79700002, "visitor_id": 19100002, "reason": "damaged", "amount": 3000.0,
         "resource_id": 29200002, "date_issued": "2026-11-22", "status": "paid"},
        {"id": 79700003, "visitor_id": 19100003, "reason": "late", "amount": 50.0,
         "resource_id": 29200003, "date_issued": "2026-12-03", "status": "unpaid"},
    ],
}
