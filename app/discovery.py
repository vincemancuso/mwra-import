import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.config import MWRA_BASE_URL
from app.errors import ReportDiscoveryError
from app.models import ReportLink

MONTHS = {
    name.lower(): number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}
MONTHS.update({name[:3]: number for name, number in tuple(MONTHS.items())})

LABEL_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?\s+((?:20)\d{2})\b",
    re.IGNORECASE,
)
FILENAME_PATTERN = re.compile(
    r"(?:update|wq)[^0-9]*(0?[1-9]|1[0-2])[-_]?((?:20\d{2})|\d{2})\b",
    re.IGNORECASE,
)


def _date_from_anchor(label: str, href: str, title: str) -> tuple[int, int] | None:
    for candidate in (label, title):
        match = LABEL_PATTERN.search(candidate)
        if match:
            month = MONTHS[match.group(1).lower().rstrip(".")]
            return month, int(match.group(2))

    match = FILENAME_PATTERN.search(f"{href} {title}")
    if match:
        month = int(match.group(1))
        year = int(match.group(2))
        if year < 100:
            year += 2000
        return month, year
    return None


def find_report_links(html: str, base_url: str = MWRA_BASE_URL) -> list[ReportLink]:
    soup = BeautifulSoup(html, "html.parser")
    reports: dict[tuple[int, int], ReportLink] = {}
    base_parts = urlparse(base_url)

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        label = " ".join(anchor.stripped_strings)
        title = anchor.get("title", "")
        combined = f"{href} {title}".lower()
        if (
            "wq" not in combined
            and "update" not in combined
            and "/media/file/" not in href
            and not LABEL_PATTERN.search(label)
        ):
            continue

        parsed = _date_from_anchor(label, href, title)
        if not parsed:
            continue
        month, year = parsed
        report_url = urljoin(base_url, href)
        report_parts = urlparse(report_url)
        if (
            report_parts.scheme not in {"http", "https"}
            or report_parts.netloc != base_parts.netloc
        ):
            continue
        reports[(year, month)] = ReportLink(
            month=month,
            year=year,
            label=label or datetime(year, month, 1).strftime("%b %Y"),
            url=report_url,
        )

    return sorted(reports.values(), key=lambda report: report.report_date)


def select_latest_report(html: str, base_url: str = MWRA_BASE_URL) -> ReportLink:
    reports = find_report_links(html, base_url)
    if not reports:
        raise ReportDiscoveryError(
            "No linked monthly MWRA water-quality PDFs were found. "
            "The MWRA page layout may have changed."
        )
    return reports[-1]
