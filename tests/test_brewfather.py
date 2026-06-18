from datetime import UTC, datetime

import pytest

from xml.etree import ElementTree as ET

from app.brewfather import (
    beerxml_filename,
    brewfather_filename,
    build_beerxml,
    build_brewfather_recipe,
)
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
    repeated_recipe = build_brewfather_recipe(profile)

    assert recipe["name"] == "Dummy MWRA April 2026 Recipe"
    assert repeated_recipe == recipe
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

    xml = build_beerxml(recipe)
    root = ET.fromstring(xml)
    xml_recipe = root.find("RECIPE")
    assert xml_recipe is not None
    assert xml_recipe.findtext("NAME") == recipe["name"]
    assert xml_recipe.findtext("BREWER") in (None, "")
    assert xml_recipe.findtext("BATCH_SIZE") == str(recipe["batchSize"])
    assert xml_recipe.findtext("EQUIPMENT/NAME") == recipe["equipment"]["name"]

    water = xml_recipe.find("WATERS/WATER")
    assert water is not None
    assert water.findtext("NAME") == source["name"]
    assert float(water.findtext("CALCIUM")) == source["calcium"]
    assert float(water.findtext("MAGNESIUM")) == source["magnesium"]
    assert float(water.findtext("SODIUM")) == source["sodium"]
    assert float(water.findtext("CHLORIDE")) == source["chloride"]
    assert float(water.findtext("SULFATE")) == source["sulfate"]
    assert float(water.findtext("BICARBONATE")) == source["bicarbonate"]
    assert float(water.findtext("PH")) == source["ph"]

    assert beerxml_filename(profile) == (
        "Brewfather_BeerXML_Dummy_MWRA_April_2026_Recipe.xml"
    )
