"""Delete the local MWRA CSV database and cached report PDFs.

This script intentionally uses only the Python standard library so it can run
even when the FastAPI app dependencies are not installed yet.

Run from the project root:

    python clear_local_data.py
"""

from __future__ import annotations

import csv
import re
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "app-config.toml"
RAW_VALUES_CSV = PROJECT_ROOT / "data" / "mwra-treated-water-values.csv"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
DEFAULT_MWRA_REPORTS_PAGE_URL = (
    "https://www.mwra.com/your-water-system/drinking-water-quality/"
    "monthly-water-quality-test-results"
)
USER_AGENT = "MWRA Homebrewing Water Profile maintenance script"
CONFIRMATION = "DELETE MWRA DATA"

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


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href")
        if href:
            self._current_href = href
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current_href:
            self.links.append((self._current_href, " ".join(self._current_text)))
            self._current_href = None
            self._current_text = []


def load_report_page_url() -> str:
    if not CONFIG_PATH.exists():
        return DEFAULT_MWRA_REPORTS_PAGE_URL
    with CONFIG_PATH.open("rb") as handle:
        config = tomllib.load(handle)
    return str(config.get("mwra_reports_page_url") or DEFAULT_MWRA_REPORTS_PAGE_URL)


def month_from_link(label: str, href: str) -> str | None:
    match = LABEL_PATTERN.search(label)
    if match:
        month = MONTHS[match.group(1).lower().rstrip(".")]
        return f"{int(match.group(2)):04d}-{month:02d}"

    match = FILENAME_PATTERN.search(href)
    if not match:
        return None
    month = int(match.group(1))
    year = int(match.group(2))
    if year < 100:
        year += 2000
    return f"{year:04d}-{month:02d}"


def linked_report_months() -> set[str] | None:
    try:
        source_url = load_report_page_url()
        request = Request(source_url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"Could not check the current MWRA website: {exc}")
        return None

    parser = LinkParser()
    parser.feed(html)
    months: set[str] = set()
    for href, label in parser.links:
        absolute_href = urljoin(source_url, href)
        parsed = month_from_link(label, absolute_href)
        if parsed:
            months.add(parsed)
    return months


def cached_report_months() -> set[str]:
    if not RAW_VALUES_CSV.exists():
        return set()
    with RAW_VALUES_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
    return {column for column in header if re.fullmatch(r"20\d{2}-\d{2}", column)}


def cached_pdfs() -> list[Path]:
    if not REPORTS_DIR.exists():
        return []
    return sorted(REPORTS_DIR.glob("*.pdf"))


def main() -> int:
    csv_months = cached_report_months()
    pdfs = cached_pdfs()
    linked_months = linked_report_months()

    print("WARNING: this will permanently remove local MWRA cached data.")
    print()
    print(f"CSV database: {RAW_VALUES_CSV}")
    print(f"Cached PDF directory: {REPORTS_DIR}")
    print(f"CSV month columns found: {len(csv_months)}")
    print(f"Cached PDFs found: {len(pdfs)}")
    print()
    print(
        "If MWRA no longer publishes one of these reports, deleted values may "
        "not be recoverable from the MWRA website."
    )

    if linked_months is None:
        print(
            "Because the MWRA website could not be checked, this script cannot "
            "tell you which cached months are still recoverable."
        )
    else:
        unavailable = sorted(csv_months - linked_months)
        if unavailable:
            print()
            print("Cached CSV months not currently linked on the MWRA page:")
            for month in unavailable:
                print(f"  - {month}")
            print("Deleting now may permanently remove those local values.")
        else:
            print("All cached CSV months are currently linked on the MWRA page.")

    print()
    entered = input(f'Type "{CONFIRMATION}" to continue: ')
    if entered != CONFIRMATION:
        print("Canceled. No local data was removed.")
        return 1

    if RAW_VALUES_CSV.exists():
        RAW_VALUES_CSV.unlink()
        print(f"Deleted {RAW_VALUES_CSV}")
    else:
        print("No CSV database found.")

    for pdf in pdfs:
        pdf.unlink()
        print(f"Deleted {pdf}")

    print("Done. Local MWRA CSV data and cached PDFs have been removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
