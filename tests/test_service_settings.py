from pathlib import Path

import httpx
import pytest

from app.service import WaterProfileService
from app.settings import AppSettings
from app.models import RawMeasurement
from app.report_store import RawValueStore

FIXTURES = Path(__file__).parent / "fixtures"


def raw_measurements(calcium: float) -> dict[str, RawMeasurement]:
    values = {
        "calcium": (calcium, "UG/L"),
        "magnesium": (845, "UG/L"),
        "sodium": (34, "MG/L"),
        "chloride": (27.3, "MG/L"),
        "sulfate": (5.6, "MG/L"),
        "alkalinity": (40.3, "MG/L"),
        "ph": (9.7, "standard units"),
    }
    return {
        key: RawMeasurement(
            parameter=key.title(),
            value=value,
            unit=unit,
            source_label="Metro-Boston treated/finished water",
        )
        for key, (value, unit) in values.items()
    }


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


@pytest.mark.asyncio
async def test_service_reuses_csv_values_without_redownloading_cached_report(
    tmp_path: Path,
):
    requested_urls: list[str] = []
    pdf_bytes = (FIXTURES / "mwra-report.pdf").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).endswith("/monthly"):
            return httpx.Response(
                200,
                text='<a href="/reports/wq-update-042026.pdf">April 2026</a>',
            )
        return httpx.Response(
            200,
            content=pdf_bytes,
            headers={"content-type": "application/pdf"},
        )

    settings = AppSettings(
        mwra_reports_page_url="https://water.example.test/monthly",
        main_profile_fields=["calcium"],
    )
    csv_path = tmp_path / "mwra-values.csv"

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        first_service = WaterProfileService(
            settings=settings,
            reports_dir=tmp_path / "reports",
            raw_values_csv=csv_path,
            client=client,
        )
        first_profile, _ = await first_service.latest()

    assert first_profile.brewfather_values.calcium == 4.37
    assert "https://water.example.test/reports/wq-update-042026.pdf" in requested_urls
    assert csv_path.exists()
    assert "2026-04" in csv_path.read_text(encoding="utf-8")

    requested_urls.clear()

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        second_service = WaterProfileService(
            settings=settings,
            reports_dir=tmp_path / "empty-reports",
            raw_values_csv=csv_path,
            client=client,
        )
        second_profile, _ = await second_service.latest()

    assert second_profile.brewfather_values.calcium == 4.37
    assert requested_urls == ["https://water.example.test/monthly"]


@pytest.mark.asyncio
async def test_history_uses_csv_months_that_are_no_longer_linked(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text='<a href="/reports/wq-update-042026.pdf">April 2026</a>',
        )

    csv_path = tmp_path / "mwra-values.csv"
    store = RawValueStore(csv_path)
    store.save_month(2025, 12, raw_measurements(4200))
    store.save_month(2026, 4, raw_measurements(4370))

    settings = AppSettings(
        mwra_reports_page_url="https://water.example.test/monthly",
        main_profile_fields=["calcium"],
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = WaterProfileService(
            settings=settings,
            reports_dir=tmp_path / "reports",
            raw_values_csv=csv_path,
            client=client,
        )
        history = await service.history()

    assert [point.month_year for point in history.series[0].points] == [
        "December 2025",
        "April 2026",
    ]
