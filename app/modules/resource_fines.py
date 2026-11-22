from datetime import date

LATE_FINE_PER_DAY = 50

@staticmethod
def calculate_fine(expectedDate, actualDate):
    """
    Calculate the fine based on the expected and actual return dates.

    :param expectedDate: The date when the resource was expected to be returned.
    :param actualDate: The date when the resource was actually returned.
    :return: The calculated fine amount.
    """
    if actualDate <= expectedDate:
        return 0
    else:
        days_late = max(0, (actualDate - expectedDate).days)
        return days_late * LATE_FINE_PER_DAY

def __init__():
def _require_staff():
def _to_date():
def _get():
def _is_active_loan():
def _active_loan_for():
def calculate_late_fine():
def _new_fine():
def _replacement_cost():
def _describe():
def record_return():
def lost_or_damaged():
def unpaid_fines():
def list_fines():
def active_loans():
def list_visitors():
def resources_condition():
def confirm_payment():
def generate_receipt():
def _issue_receipt():