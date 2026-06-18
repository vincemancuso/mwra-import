import asyncio
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import (
    DEFAULT_COLUMN,
    HTTP_TIMEOUT_SECONDS,
    MWRA_MONTHLY_URL,
    REPORTS_DIR,
    USER_AGENT,
)
from app.conversions import convert_measurements
from app.discovery import select_latest_report
from app.errors import ReportDiscoveryError, ReportDownloadError
from app.models import ReportLink, ReportMetadata, WaterProfileResponse
from app.parser import parse_report_pdf


class WaterProfileService:
    def __init__(
        self,
        source_url: str = MWRA_MONTHLY_URL,
        reports_dir: Path = REPORTS_DIR,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.source_url = source_url
        self.reports_dir = reports_dir
        self._client = client
        self._lock = asyncio.Lock()
        self._latest: tuple[WaterProfileResponse, Path] | None = None

    async def _request(self, url: str) -> httpx.Response:
        if self._client:
            return await self._client.get(url, follow_redirects=True)
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            return await client.get(url)

    async def discover(self) -> ReportLink:
        try:
            response = await self._request(self.source_url)
            response.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise ReportDiscoveryError(
                f"Could not fetch the MWRA monthly reports page: {exc}"
            ) from exc
        return select_latest_report(response.text)

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
                f"Could not download the latest MWRA report ({report.month_year}): {exc}"
            ) from exc
        if not response.content.startswith(b"%PDF"):
            raise ReportDownloadError(
                "The latest MWRA report link did not return a PDF. "
                "The MWRA website may have changed."
            )
        destination.write_bytes(response.content)
        return destination

    async def latest(self, force_refresh: bool = False) -> tuple[WaterProfileResponse, Path]:
        async with self._lock:
            if self._latest and not force_refresh:
                return self._latest

            report = await self.discover()
            pdf_path = await self.cache_pdf(report)
            raw = await asyncio.to_thread(parse_report_pdf, pdf_path)
            brewfather, conversions = convert_measurements(raw)
            profile = WaterProfileResponse(
                name=f"MWRA Metro-Boston Tap Water - {report.month_year}",
                report=ReportMetadata(
                    report_month=report.report_date.strftime("%B"),
                    report_year=report.year,
                    report_label=report.label,
                    source_page_url=self.source_url,
                    source_pdf_url=report.url,
                    selected_column=DEFAULT_COLUMN,
                    cached_filename=pdf_path.name,
                    fetched_at=datetime.now(UTC),
                ),
                raw_values=raw,
                conversions=conversions,
                brewfather_values=brewfather,
            )
            self._latest = (profile, pdf_path)
            return self._latest
