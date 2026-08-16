import asyncio
import calendar
import csv
from io import StringIO
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import (
    DEFAULT_COLUMN,
    HTTP_TIMEOUT_SECONDS,
    RAW_VALUES_CSV,
    REPORTS_DIR,
    USER_AGENT,
)
from app.conversions import convert_measurements
from app.discovery import find_report_links
from app.errors import (
    ReportDiscoveryError,
    ReportDownloadError,
    ReportNotFoundError,
    WaterProfileError,
)
from app.models import (
    HistoryPoint,
    HistorySeries,
    ReportCatalog,
    ReportLink,
    ReportMetadata,
    SkippedHistoryReport,
    WaterProfileHistoryResponse,
    WaterProfileResponse,
)
from app.parser import parse_report_pdf_details
from app.report_store import RawValueStore, merge_measurements, month_key
from app.settings import AppSettings
from app.water_context import build_profile_measurements, measurement_key


REQUIRED_RAW_KEYS = {
    "calcium",
    "magnesium",
    "sodium",
    "chloride",
    "sulfate",
    "alkalinity",
    "ph",
}

BREWING_EXPORT_FIELDS = [
    ("calcium", "Calcium", "ppm"),
    ("magnesium", "Magnesium", "ppm"),
    ("sodium", "Sodium", "ppm"),
    ("chloride", "Chloride", "ppm"),
    ("sulfate", "Sulfate", "ppm"),
    ("bicarbonate", "Bicarbonate", "ppm"),
    ("ph", "pH", "pH"),
]


class WaterProfileService:
    def __init__(
        self,
        settings: AppSettings,
        reports_dir: Path = REPORTS_DIR,
        raw_values_csv: Path = RAW_VALUES_CSV,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.source_url = str(settings.mwra_reports_page_url)
        self.reports_dir = reports_dir
        self.store = RawValueStore(raw_values_csv)
        self._client = client
        self._lock = asyncio.Lock()
        self._catalog: ReportCatalog | None = None
        self._profiles: dict[
            tuple[int, int], tuple[WaterProfileResponse, Path]
        ] = {}
        self._store_errors: dict[str, str] = {}

    async def _request(self, url: str) -> httpx.Response:
        if self._client:
            return await self._client.get(url, follow_redirects=True)
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            return await client.get(url)

    async def discover(self) -> ReportCatalog:
        try:
            response = await self._request(self.source_url)
            response.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise ReportDiscoveryError(
                f"Could not fetch the MWRA monthly reports page: {exc}"
            ) from exc
        reports = find_report_links(response.text, self.source_url)
        if not reports:
            raise ReportDiscoveryError(
                "No linked monthly MWRA water-quality PDFs were found. "
                "The MWRA page layout may have changed."
            )
        reports.reverse()
        return ReportCatalog(reports=reports, latest=reports[0])

    async def reports(self, force_refresh: bool = False) -> ReportCatalog:
        async with self._lock:
            if self._catalog is None or force_refresh:
                self._catalog = await self.discover()
            await self._ensure_store_current(force_refresh=force_refresh)
            return self._catalog

    async def cache_pdf(self, report: ReportLink) -> Path:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        destination = self.reports_dir / report.cache_filename
        if destination.exists() and destination.stat().st_size > 4:
            if destination.read_bytes()[:4] == b"%PDF":
                return destination

        try:
            response = await self._request(report.url)
            response.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise ReportDownloadError(
                f"Could not download the MWRA report ({report.month_year}): {exc}"
            ) from exc
        if not response.content.startswith(b"%PDF"):
            raise ReportDownloadError(
                "The selected MWRA report link did not return a PDF. "
                "The MWRA website may have changed."
            )
        destination.write_bytes(response.content)
        return destination

    async def _parse_and_store_report(self, report: ReportLink) -> Path:
        pdf_path = await self.cache_pdf(report)
        raw, other_values = await asyncio.to_thread(parse_report_pdf_details, pdf_path)
        other_by_key = [
            (measurement_key(measurement.parameter), measurement)
            for measurement in other_values
        ]
        self.store.save_month(
            report.year,
            report.month,
            merge_measurements(raw, other_by_key),
        )
        self._profiles.pop((report.year, report.month), None)
        return pdf_path

    async def _ensure_store_current(self, force_refresh: bool = False) -> None:
        if self._catalog is None:
            self._catalog = await self.discover()

        existing_months = set(self.store.month_columns())
        for report in reversed(self._catalog.reports):
            report_month = month_key(report.year, report.month)
            if force_refresh or report_month not in existing_months:
                try:
                    await self._parse_and_store_report(report)
                    existing_months.add(report_month)
                    self._store_errors.pop(report_month, None)
                except WaterProfileError as exc:
                    self._store_errors[report_month] = str(exc)

    def _build_profile_from_store(
        self, report: ReportLink, pdf_path: Path
    ) -> WaterProfileResponse:
        raw_all = self.store.load_month(report.year, report.month)
        raw = {key: raw_all[key] for key in REQUIRED_RAW_KEYS if key in raw_all}
        other_values = [
            measurement
            for key, measurement in raw_all.items()
            if key not in REQUIRED_RAW_KEYS
        ]
        brewfather, conversions = convert_measurements(raw)
        profile_values, hidden_values = build_profile_measurements(
            brewfather,
            other_values,
            self.settings.main_profile_fields,
        )
        return WaterProfileResponse(
            name=f"MWRA Metro-Boston Tap Water - {report.month_year}",
            report=ReportMetadata(
                report_month=report.report_date.strftime("%B"),
                report_month_number=report.month,
                report_year=report.year,
                report_label=report.label,
                source_page_url=self.source_url,
                source_pdf_url=report.url,
                selected_column=DEFAULT_COLUMN,
                cached_filename=pdf_path.name,
                fetched_at=datetime.now(UTC),
            ),
            raw_values=raw,
            profile_values=profile_values,
            other_values=hidden_values,
            conversions=conversions,
            brewfather_values=brewfather,
        )

    async def _build_profile(
        self, report: ReportLink, force_refresh: bool = False
    ) -> tuple[WaterProfileResponse, Path]:
        key = (report.year, report.month)
        if key in self._profiles and not force_refresh:
            return self._profiles[key]

        if force_refresh or not self.store.has_month(report.year, report.month):
            pdf_path = await self._parse_and_store_report(report)
        else:
            pdf_path = self.reports_dir / report.cache_filename
        result = (self._build_profile_from_store(report, pdf_path), pdf_path)
        self._profiles[key] = result
        return result

    async def profile(
        self, year: int, month: int, force_refresh: bool = False
    ) -> tuple[WaterProfileResponse, Path]:
        async with self._lock:
            if self._catalog is None:
                self._catalog = await self.discover()
            await self._ensure_store_current(force_refresh=force_refresh)
            report = next(
                (
                    candidate
                    for candidate in self._catalog.reports
                    if candidate.year == year and candidate.month == month
                ),
                None,
            )
            if report is None:
                raise ReportNotFoundError(
                    f"No linked MWRA monthly report was found for {year:04d}-{month:02d}."
                )
            return await self._build_profile(report)

    async def latest(
        self, force_refresh: bool = False
    ) -> tuple[WaterProfileResponse, Path]:
        async with self._lock:
            if self._catalog is None or force_refresh:
                self._catalog = await self.discover()
            await self._ensure_store_current(force_refresh=force_refresh)
            return await self._build_profile(self._catalog.latest)

    async def history(self) -> WaterProfileHistoryResponse:
        async with self._lock:
            if self._catalog is None:
                self._catalog = await self.discover()
            await self._ensure_store_current()

            profiles: list[tuple[int, int, list]] = []
            skipped_reports: list[SkippedHistoryReport] = []
            report_by_month = {
                month_key(report.year, report.month): report
                for report in self._catalog.reports
            }
            for stored_month in self.store.sorted_month_columns():
                year, month = (int(part) for part in stored_month.split("-"))
                try:
                    raw_all = self.store.load_month(year, month)
                    raw = {
                        key: raw_all[key]
                        for key in REQUIRED_RAW_KEYS
                        if key in raw_all
                    }
                    other_values = [
                        measurement
                        for key, measurement in raw_all.items()
                        if key not in REQUIRED_RAW_KEYS
                    ]
                    brewfather, _ = convert_measurements(raw)
                    profile_values, _ = build_profile_measurements(
                        brewfather,
                        other_values,
                        self.settings.main_profile_fields,
                    )
                    profiles.append((year, month, profile_values))
                except Exception as exc:
                    report = report_by_month.get(stored_month)
                    skipped_reports.append(
                        SkippedHistoryReport(
                            month=month,
                            year=year,
                            month_year=(
                                report.month_year
                                if report
                                else f"{calendar.month_name[month]} {year}"
                            ),
                            error=str(exc),
                        )
                    )

            series: list[HistorySeries] = []
            for field_key in self.settings.main_profile_fields:
                measurements = [
                    next(
                        (
                            measurement
                            for measurement in profile_values
                            if measurement.key == field_key
                        ),
                        None,
                    )
                    for _, _, profile_values in profiles
                ]
                paired = [
                    (year, month, measurement)
                    for (year, month, _), measurement in zip(
                        profiles, measurements, strict=True
                    )
                    if measurement is not None
                ]
                if not paired:
                    continue

                values = [measurement.value for _, _, measurement in paired]
                min_value = min(values)
                max_value = max(values)
                spread = max_value - min_value
                representative = paired[-1][2]
                points = [
                    HistoryPoint(
                        report_month=calendar.month_name[month],
                        report_month_number=month,
                        report_year=year,
                        month_year=(
                            f"{calendar.month_name[month]} {year}"
                        ),
                        value=measurement.value,
                        normalized=(
                            0.5
                            if spread == 0
                            else (measurement.value - min_value) / spread
                        ),
                    )
                    for year, month, measurement in paired
                ]
                series.append(
                    HistorySeries(
                        key=field_key,
                        label=representative.label,
                        unit=representative.unit,
                        description=representative.description,
                        min_value=min_value,
                        max_value=max_value,
                        points=points,
                    )
                )

            return WaterProfileHistoryResponse(
                source_page_url=self.source_url,
                normalized_scale=(
                    "The browser charts each field on a fixed brewing-reference "
                    "scale and lets users switch between rolling, year-to-date, "
                    "and all-time intervals."
                ),
                series=series,
                skipped_reports=skipped_reports,
            )

    async def brewing_values_csv(self) -> str:
        async with self._lock:
            if self._catalog is None:
                self._catalog = await self.discover()
            await self._ensure_store_current()

            months = self.store.sorted_month_columns()
            output = StringIO()
            fieldnames = ["key", "parameter", "unit", *months]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            values_by_month: dict[str, dict[str, float]] = {}
            for stored_month in months:
                year, month = (int(part) for part in stored_month.split("-"))
                try:
                    raw_all = self.store.load_month(year, month)
                    raw = {
                        key: raw_all[key]
                        for key in REQUIRED_RAW_KEYS
                        if key in raw_all
                    }
                    brewfather, _ = convert_measurements(raw)
                    values_by_month[stored_month] = {
                        "calcium": brewfather.calcium,
                        "magnesium": brewfather.magnesium,
                        "sodium": brewfather.sodium,
                        "chloride": brewfather.chloride,
                        "sulfate": brewfather.sulfate,
                        "bicarbonate": brewfather.bicarbonate,
                        "ph": brewfather.ph,
                    }
                except Exception:
                    values_by_month[stored_month] = {}

            for key, label, unit in BREWING_EXPORT_FIELDS:
                row = {"key": key, "parameter": label, "unit": unit}
                row.update(
                    {
                        stored_month: (
                            f"{values_by_month[stored_month][key]:g}"
                            if key in values_by_month[stored_month]
                            else ""
                        )
                        for stored_month in months
                    }
                )
                writer.writerow(row)

            return output.getvalue()

    async def raw_values_csv(self) -> str:
        async with self._lock:
            if self._catalog is None:
                self._catalog = await self.discover()
            await self._ensure_store_current()

            header, rows = self.store.export_rows()
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=header)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in header})
            return output.getvalue()
