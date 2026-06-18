from datetime import UTC, datetime

import pytest

from app.brewfather import brewfather_filename, build_brewfather_recipe
from app.models import (
    BrewfatherValues,
    RawMeasurement,
    ReportMetadata,
    WaterProfileResponse,
)


def test_builds_blank_attribution_recipe_with_selected_water_profile():
    profile = WaterProfileResponse(
        name="MWRA Metro-Boston Tap Water - April 2026",
        report=ReportMetadata(
            report_month="April",
            report_month_number=4,
            report_year=2026,
            report_label="Apr 2026",
            source_page_url="https://www.mwra.test/monthly",
            source_pdf_url="https://www.mwra.test/april.pdf",
            selected_column="Metro-Boston treated",
            cached_filename="april.pdf",
            fetched_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
        raw_values={
            "alkalinity": RawMeasurement(
                parameter="Alkalinity",
                value=40.3,
                unit="MG/L",
                source_label="fixture",
            )
        },
        conversions=[],
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

    recipe = build_brewfather_recipe(profile)

    assert recipe["name"] == "Dummy MWRA April 2026 Recipe"
    assert recipe["author"] == ""
    assert recipe["tags"] is None
    assert recipe["searchTags"] == []
    assert recipe["water"]["mashPh"] is None
    assert recipe["water"]["mashPhDistilled"] is None
    assert brewfather_filename(profile) == (
        "Brewfather_RECIPE_Dummy_MWRA_April_2026_Recipe.json"
    )

    source = recipe["water"]["source"]
    assert source["name"] == "MWRA Metro-Boston - April 2026"
    assert source["alkalinity"] == 40.3
    assert source["calcium"] == 4.37
    assert source["magnesium"] == 0.84
    assert source["sodium"] == 34
    assert source["chloride"] == 27.3
    assert source["sulfate"] == 5.6
    assert source["bicarbonate"] == 49.17
    assert source["ph"] == 9.7
    assert source["soClRatio"] == pytest.approx(0.21)

    for key in ("mash", "sparge", "total"):
        assert recipe["water"][key] == source
