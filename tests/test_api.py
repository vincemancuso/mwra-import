from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.errors import ReportNotFoundError
from app.main import app
from app.models import (
    BrewfatherValues,
    Conversion,
    RawMeasurement,
    ReportMetadata,
    ReportCatalog,
    ReportLink,
    WaterProfileResponse,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureService:
    def _profile(self, year=2026, month=4):
        raw = RawMeasurement(
            parameter="Calcium",
            value=4370,
            unit="UG/L",
            source_label="fixture",
        )
        profile = WaterProfileResponse(
            name=f"MWRA Metro-Boston Tap Water - {'April' if month == 4 else 'March'} {year}",
            report=ReportMetadata(
                report_month="April" if month == 4 else "March",
                report_month_number=month,
                report_year=year,
                report_label=f"{'Apr' if month == 4 else 'Mar'} {year}",
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

    async def reports(self):
        reports = [
            ReportLink(
                month=4,
                year=2026,
                label="Apr 2026",
                url="https://www.mwra.test/april.pdf",
            ),
            ReportLink(
                month=3,
                year=2026,
                label="Mar 2026",
                url="https://www.mwra.test/march.pdf",
            ),
        ]
        return ReportCatalog(reports=reports, latest=reports[0])

    async def profile(self, year: int, month: int):
        if (year, month) not in {(2026, 4), (2026, 3)}:
            raise ReportNotFoundError("No linked fixture report was found.")
        return self._profile(year, month)

    async def latest(self):
        return self._profile()


def test_ui_and_api_endpoints():
    with TestClient(app) as client:
        client.app.state.profile_service = FixtureService()

        page = client.get("/")
        reports = client.get("/api/reports")
        selected = client.get("/api/reports/2026/3")
        selected_pdf = client.get("/api/reports/2026/3/pdf")
        brewfather = client.get("/api/reports/2026/3/brewfather.json")
        missing = client.get("/api/reports/2025/12")
        api = client.get("/api/latest")
        pdf = client.get("/api/latest/pdf")

    assert page.status_code == 200
    assert "MWRA Brewfather Water Profile" in page.text
    assert 'id="report-select"' in page.text
    assert reports.status_code == 200
    assert reports.json()["latest"]["month"] == 4
    assert reports.json()["reports"][1]["month_year"] == "March 2026"
    assert selected.status_code == 200
    assert selected.json()["report"]["report_month"] == "March"
    assert selected_pdf.status_code == 200
    assert brewfather.status_code == 200
    assert "attachment" in brewfather.headers["content-disposition"]
    recipe = brewfather.json()
    assert recipe["name"] == "Dummy MWRA March 2026 Recipe"
    assert recipe["author"] == ""
    assert recipe["tags"] is None
    assert recipe["searchTags"] == []
    for water_key in ("source", "mash", "sparge", "total"):
        assert recipe["water"][water_key]["calcium"] == 4.37
        assert recipe["water"][water_key]["bicarbonate"] == 49.17
        assert recipe["water"][water_key]["ph"] == 9.7
    assert missing.status_code == 404
    assert api.status_code == 200
    assert api.json()["brewfather_values"]["pH"] == 9.7
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
