import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import (
    DEFAULT_COLUMN,
    HTTP_TIMEOUT_SECONDS,
    REPORTS_DIR,
    USER_AGENT,
)
from app.conversions import convert_measurements
from app.discovery import find_report_links
from app.errors import (
    ReportDiscoveryError,
    ReportDownloadError,
    ReportNotFoundError,
)
from app.models import ReportCatalog, ReportLink, ReportMetadata, WaterProfileResponse
from app.parser import parse_report_pdf_details
from app.settings import AppSettings
from app.water_context import build_profile_measurements


class WaterProfileService:
    def __init__(
        self,
        settings: AppSettings,
        reports_dir: Path = REPORTS_DIR,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.source_url = str(settings.mwra_reports_page_url)
        self.reports_dir = reports_dir
        self._client = client
        self._lock = asyncio.Lock()
        self._catalog: ReportCatalog | None = None
        self._profiles: dict[
            tuple[int, int], tuple[WaterProfileResponse, Path]
        ] = {}

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

    async def _build_profile(
        self, report: ReportLink, force_refresh: bool = False
    ) -> tuple[WaterProfileResponse, Path]:
        key = (report.year, report.month)
        if key in self._profiles and not force_refresh:
            return self._profiles[key]

        pdf_path = await self.cache_pdf(report)
        raw, other_values = await asyncio.to_thread(parse_report_pdf_details, pdf_path)
        brewfather, conversions = convert_measurements(raw)
        profile_values, hidden_values = build_profile_measurements(
            brewfather,
            other_values,
            self.settings.main_profile_fields,
        )
        result = (
            WaterProfileResponse(
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
            ),
            pdf_path,
        )
        self._profiles[key] = result
        return result

    async def profile(
        self, year: int, month: int, force_refresh: bool = False
    ) -> tuple[WaterProfileResponse, Path]:
        async with self._lock:
            if self._catalog is None:
                self._catalog = await self.discover()
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
            return await self._build_profile(report, force_refresh)

    async def latest(
        self, force_refresh: bool = False
    ) -> tuple[WaterProfileResponse, Path]:
        async with self._lock:
            if self._catalog is None or force_refresh:
                self._catalog = await self.discover()
            return await self._build_profile(self._catalog.latest, force_refresh)
