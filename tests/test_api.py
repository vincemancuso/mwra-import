from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    BrewfatherValues,
    Conversion,
    RawMeasurement,
    ReportMetadata,
    WaterProfileResponse,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureService:
    async def latest(self):
        raw = RawMeasurement(
            parameter="Calcium",
            value=4370,
            unit="UG/L",
            source_label="fixture",
        )
        profile = WaterProfileResponse(
            name="MWRA Metro-Boston Tap Water - April 2026",
            report=ReportMetadata(
                report_month="April",
                report_year=2026,
                report_label="Apr 2026",
                source_page_url="https://www.mwra.test/monthly",
                source_pdf_url="https://www.mwra.test/report.pdf",
                selected_column="Metro-Boston treated",
                cached_filename="mwra-report.pdf",
                fetched_at=datetime(2026, 5, 1, tzinfo=UTC),
            ),
            raw_values={"calcium": raw},
            conversions=[
                Conversion(
                    field="calcium",
                    source_parameter="Calcium",
                    source_value=4370,
                    source_unit="UG/L",
                    formula="ug/L ÷ 1000 = ppm",
                    result=4.37,
                    result_unit="ppm",
                )
            ],
            brewfather_values=BrewfatherValues(
                calcium=4.37,
                magnesium=0.84,
                sodium=34,
                chloride=27.3,
                sulfate=5.6,
                bicarbonate=49.17,
                pH=9.7,
            ),
        )
        return profile, FIXTURES / "mwra-report.pdf"


def test_ui_and_api_endpoints():
    with TestClient(app) as client:
        client.app.state.profile_service = FixtureService()

        page = client.get("/")
        api = client.get("/api/latest")
        pdf = client.get("/api/latest/pdf")

    assert page.status_code == 200
    assert "MWRA Brewfather Water Profile" in page.text
    assert api.status_code == 200
    assert api.json()["brewfather_values"]["pH"] == 9.7
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
