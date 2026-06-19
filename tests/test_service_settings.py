from pathlib import Path

import httpx
import pytest

from app.service import WaterProfileService
from app.settings import AppSettings


@pytest.mark.asyncio
async def test_configured_report_page_is_used_for_discovery_and_relative_links(
    tmp_path: Path,
):
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(
            200,
            text='<a href="/reports/wq-update-042026">April 2026</a>',
        )

    settings = AppSettings(
        mwra_reports_page_url="https://water.example.test/monthly",
        main_profile_fields=["calcium"],
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = WaterProfileService(
            settings=settings,
            reports_dir=tmp_path,
            client=client,
        )
        catalog = await service.discover()

    assert requested_urls == ["https://water.example.test/monthly"]
    assert catalog.latest.url == "https://water.example.test/reports/wq-update-042026"
