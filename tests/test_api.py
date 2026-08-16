from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.errors import ReportNotFoundError
from app.main import app
from app.models import (
    BrewfatherValues,
    Conversion,
    ProfileMeasurement,
    RawMeasurement,
    ReportMetadata,
    ReportCatalog,
    ReportLink,
    WaterProfileHistoryResponse,
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
            profile_values=[
                ProfileMeasurement(
                    key="calcium",
                    label="Calcium",
                    value=4.37,
                    unit="ppm",
                    description="Calcium brewing context.",
                )
            ],
            other_values=[
                ProfileMeasurement(
                    key="hardness",
                    label="Hardness",
                    value=14.4,
                    unit="MG/L",
                    description="Hardness brewing context.",
                )
            ],
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

    async def history(self):
        march_profile, _ = self._profile(2026, 3)
        april_profile, _ = self._profile(2026, 4)
        march_profile.profile_values[0].value = 4.0
        return WaterProfileHistoryResponse(
            source_page_url="https://www.mwra.test/monthly",
            normalized_scale="Each line is independently normalized for fixture tests.",
            series=[
                {
                    "key": "calcium",
                    "label": "Calcium",
                    "unit": "ppm",
                    "description": "Calcium brewing context.",
                    "min_value": 4.0,
                    "max_value": 4.37,
                    "points": [
                        {
                            "report_month": "March",
                            "report_month_number": 3,
                            "report_year": 2026,
                            "month_year": "March 2026",
                            "value": 4.0,
                            "normalized": 0,
                        },
                        {
                            "report_month": "April",
                            "report_month_number": 4,
                            "report_year": 2026,
                            "month_year": "April 2026",
                            "value": 4.37,
                            "normalized": 1,
                        },
                    ],
                }
            ],
        )

    async def brewing_values_csv(self):
        return (
            "key,parameter,unit,2026-03,2026-04\r\n"
            "calcium,Calcium,ppm,4,4.37\r\n"
            "ph,pH,pH,9.6,9.7\r\n"
        )

    async def raw_values_csv(self):
        return (
            "key,parameter,unit,source_label,2026-03,2026-04\r\n"
            "calcium,Calcium,UG/L,fixture,4000,4370\r\n"
            "hardness,Hardness,MG/L,fixture,14,14.4\r\n"
        )


def test_ui_and_api_endpoints():
    with TestClient(app) as client:
        client.app.state.profile_service = FixtureService()

        page = client.get("/")
        reports = client.get("/api/reports")
        selected = client.get("/api/reports/2026/3")
        selected_pdf = client.get("/api/reports/2026/3/pdf")
        history = client.get("/api/history")
        brewing_csv = client.get("/api/exports/brewing-values.csv")
        raw_csv = client.get("/api/exports/raw-values.csv")
        brewfather = client.get("/api/reports/2026/3/brewfather.json")
        beerxml = client.get("/api/reports/2026/3/beerxml.xml")
        missing = client.get("/api/reports/2025/12")
        api = client.get("/api/latest")
        pdf = client.get("/api/latest/pdf")

    assert page.status_code == 200
    assert "MWRA Homebrewing Water Profile" in page.text
    assert "Boston Wort Processors Present:" in page.text
    assert 'id="report-select"' in page.text
    assert "MWRA units" in page.text
    assert "About the Brewfather JSON export" in page.text
    assert "About the BeerXML export" in page.text
    assert "About the brewing values CSV export" in page.text
    assert "About the raw MWRA CSV export" in page.text
    assert reports.status_code == 200
    assert reports.json()["latest"]["month"] == 4
    assert reports.json()["reports"][1]["month_year"] == "March 2026"
    assert selected.status_code == 200
    assert selected.json()["report"]["report_month"] == "March"
    assert selected.json()["profile_values"][0]["key"] == "calcium"
    assert selected.json()["profile_values"][0]["description"]
    assert selected.json()["other_values"][0]["label"] == "Hardness"
    assert selected_pdf.status_code == 200
    assert history.status_code == 200
    assert history.json()["series"][0]["key"] == "calcium"
    assert history.json()["series"][0]["points"][0]["month_year"] == "March 2026"
    assert history.json()["series"][0]["points"][1]["normalized"] == 1
    assert brewing_csv.status_code == 200
    assert brewing_csv.headers["content-type"].startswith("text/csv")
    assert "mwra-brewing-values-ppm.csv" in brewing_csv.headers["content-disposition"]
    assert "calcium,Calcium,ppm,4,4.37" in brewing_csv.text
    assert raw_csv.status_code == 200
    assert raw_csv.headers["content-type"].startswith("text/csv")
    assert "mwra-raw-water-values.csv" in raw_csv.headers["content-disposition"]
    assert "hardness,Hardness,MG/L,fixture,14,14.4" in raw_csv.text
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
    assert beerxml.status_code == 200
    assert beerxml.headers["content-type"].startswith("application/xml")
    assert "attachment" in beerxml.headers["content-disposition"]
    assert "Dummy MWRA March 2026 Recipe" in beerxml.text
    assert "<BREWER" in beerxml.text
    assert "<CALCIUM>4.37</CALCIUM>" in beerxml.text
    assert "<HOPS" in beerxml.text
    assert "<MISCS" in beerxml.text
    assert "<YEASTS" in beerxml.text
    assert "<TYPE>Ale</TYPE>" in beerxml.text
    assert missing.status_code == 404
    assert api.status_code == 200
    assert api.json()["brewfather_values"]["pH"] == 9.7
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
