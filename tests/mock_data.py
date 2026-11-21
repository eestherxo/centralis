"""Provisional SALISES records used only for automated testing.

These records do not represent real client data.  Their field names match the
current reporting proposal and can be adjusted after the group approves the
shared data model.
"""

MOCK_REPORT_DATA = {
    "visitor": [
        {
            "visitor_id": "V-001",
            "visitor_name": "Maya Brown",
            "visitor_type": "Undergraduate",
            "visit_date": "2026-11-01",
        },
        {
            "visitor_id": "V-001",
            "visitor_name": "Maya Brown",
            "visitor_type": "Undergraduate",
            "visit_date": "2026-11-08",
        },
        {
            "visitor_id": "V-002",
            "visitor_name": "Daniel King",
            "visitor_type": "Postgraduate",
            "visit_date": "2026-11-15",
        },
        {
            "visitor_id": "V-003",
            "visitor_name": "Leah Grant",
            "visitor_type": "Outside Personnel",
            "visit_date": "2026-11-30",
        },
        {
            "visitor_id": "V-004",
            "visitor_name": "Owen Clarke",
            "visitor_type": "Organization",
            "visit_date": "2026-12-01",
        },
    ],
    "reservation": [
        {
            "reservation_id": "RS-001",
            "visitor": "Maya Brown",
            "resource": "Seminar Room 1",
            "reservation_date": "2026-11-10",
            "status": "Approved",
        },
        {
            "reservation_id": "RS-002",
            "visitor": "Daniel King",
            "resource": "Projector 1",
            "reservation_date": "2026-11-18",
            "status": "Pending",
        },
        {
            "reservation_id": "RS-003",
            "visitor": "Leah Grant",
            "resource": "Meeting Room 2",
            "reservation_date": "2026-12-02",
            "status": "Rejected",
        },
    ],
    "journal_sales": [
        {
            "sale_id": "S-001",
            "journal": "Social and Economic Studies",
            "quantity": 2,
            "sale_date": "2026-11-12",
            "total_amount": 5000.00,
        },
        {
            "sale_id": "S-002",
            "journal": "Caribbean Dialogue",
            "quantity": 1,
            "sale_date": "2026-11-20",
            "total_amount": 2500.00,
        },
        {
            "sale_id": "S-003",
            "journal": "Social and Economic Studies",
            "quantity": 1,
            "sale_date": "2026-10-31",
            "total_amount": 2500.00,
        },
    ],
    "fines": [
        {
            "fine_id": "F-001",
            "visitor": "Maya Brown",
            "fine_type": "Overdue",
            "amount": 150.00,
            "resource": "Caribbean Development",
            "date_issued": "2026-11-15",
            "payment_status": "Unpaid",
        },
        {
            "fine_id": "F-002",
            "visitor": "Daniel King",
            "fine_type": "Damaged",
            "amount": 3000.00,
            "resource": "Regional Integration",
            "date_issued": "2026-11-22",
            "payment_status": "Paid",
        },
        {
            "fine_id": "F-003",
            "visitor": "Leah Grant",
            "fine_type": "Overdue",
            "amount": 50.00,
            "resource": "Economic Survey",
            "date_issued": "2026-12-03",
            "payment_status": "Unpaid",
        },
    ],
}
