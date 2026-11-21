from pathlib import Path

from app.modules.reports import generate_report, export_report_to_word
from tests.mock_data import MOCK_REPORT_DATA


output_folder = Path("sample_word_reports")
output_folder.mkdir(exist_ok=True)

for report_type in [
    "visitor",
    "reservation",
    "journal_sales",
    "fines",
]:
    report = generate_report(
        report_type,
        MOCK_REPORT_DATA[report_type],
        "2026-11-01",
        "2026-11-30",
        "Administrator",
    )

    output_file = export_report_to_word(
        report,
        output_folder / f"{report_type}_report.docx",
    )

    print(f"Created: {output_file.resolve()}")