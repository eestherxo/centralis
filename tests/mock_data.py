"""Provisional SALISES records used only for automated testing.

These records do not represent real client data. Their field names match the
application models and JSON data store.
"""

MOCK_REPORT_DATA = {
    "visitor": [
        {
            "visitor_id": "V-001",
            "name": "Maya Brown",
            "type": "undergraduate",
            "check_in": "2026-11-01",
        },
        {
            "visitor_id": "V-001",
            "name": "Maya Brown",
            "type": "undergraduate",
            "check_in": "2026-11-08",
        },
        {
            "visitor_id": "V-002",
            "name": "Daniel King",
            "type": "postgraduate",
            "check_in": "2026-11-15",
        },
        {
            "visitor_id": "V-003",
            "name": "Leah Grant",
            "type": "external",
            "check_in": "2026-11-30",
        },
        {
            "visitor_id": "V-004",
            "name": "Owen Clarke",
            "type": "external",
            "check_in": "2026-12-01",
        },
    ],
    "reservation": [
        {
            "id": "RS-001",
            "visitor_id": "Maya Brown",
            "resource_id": "Seminar Room 1",
            "request_date": "2026-11-10",
            "status": "approved",
        },
        {
            "id": "RS-002",
            "visitor_id": "Daniel King",
            "resource_id": "Projector 1",
            "request_date": "2026-11-18",
            "status": "pending",
        },
        {
            "id": "RS-003",
            "visitor_id": "Leah Grant",
            "resource_id": "Meeting Room 2",
            "request_date": "2026-12-02",
            "status": "declined",
        },
    ],
    "journal_sales": [
        {
            "id": "S-001",
            "journal_id": "Social and Economic Studies",
            "quantity": 2,
            "date_sold": "2026-11-12",
            "sale_amount": 5000.00,
        },
        {
            "id": "S-002",
            "journal_id": "Caribbean Dialogue",
            "quantity": 1,
            "date_sold": "2026-11-20",
            "sale_amount": 2500.00,
        },
        {
            "id": "S-003",
            "journal_id": "Social and Economic Studies",
            "quantity": 1,
            "date_sold": "2026-10-31",
            "sale_amount": 2500.00,
        },
    ],
    "fines": [
        {
            "id": "F-001",
            "visitor_id": "Maya Brown",
            "reason": "late",
            "amount": 150.00,
            "resource_id": "Caribbean Development",
            "date_issued": "2026-11-15",
            "status": "unpaid",
        },
        {
            "id": "F-002",
            "visitor_id": "Daniel King",
            "reason": "damaged",
            "amount": 3000.00,
            "resource_id": "Regional Integration",
            "date_issued": "2026-11-22",
            "status": "paid",
        },
        {
            "id": "F-003",
            "visitor_id": "Leah Grant",
            "reason": "late",
            "amount": 50.00,
            "resource_id": "Economic Survey",
            "date_issued": "2026-12-03",
            "status": "unpaid",
        },
    ],
}
