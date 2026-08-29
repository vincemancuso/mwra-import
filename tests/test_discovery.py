from pathlib import Path

import pytest

from app.discovery import find_report_links, select_latest_report
from app.errors import ReportDiscoveryError

FIXTURES = Path(__file__).parent / "fixtures"


def test_latest_report_selection_is_based_on_linked_month():
    html = (FIXTURES / "monthly-reports.html").read_text()

    reports = find_report_links(html, "https://www.mwra.test")
    latest = select_latest_report(html, "https://www.mwra.test")

    assert len(reports) == 4
    assert latest.month == 4
    assert latest.year == 2026
    assert latest.url == "https://www.mwra.test/media/file/wq-update-042026"


def test_unlinked_future_placeholder_is_not_selected():
    html = '<a href="/media/file/wq-update-042026">Apr 2026</a><span>May 2026</span>'
    assert select_latest_report(html).month == 4


def test_cross_origin_report_links_are_ignored():
    html = (
        '<a href="https://evil.example/wq-update-052026.pdf">May 2026</a>'
        '<a href="/media/file/wq-update-042026.pdf">April 2026</a>'
    )

    reports = find_report_links(html, "https://www.mwra.test/monthly")

    assert [report.month for report in reports] == [4]
    assert reports[0].url == "https://www.mwra.test/media/file/wq-update-042026.pdf"


def test_missing_reports_has_clear_error():
    with pytest.raises(ReportDiscoveryError, match="No linked monthly"):
        select_latest_report("<html><body>No reports yet</body></html>")
