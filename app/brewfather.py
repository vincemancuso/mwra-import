import base64
import copy
import gzip
import json
import uuid
from functools import lru_cache
from xml.etree import ElementTree as ET

from app.models import WaterProfileResponse

# Sanitized, gzipped template derived from the user-provided Brewfather blank
# recipe export. Personal location, equipment notes, IDs, and timestamps were
# removed before embedding it.
_TEMPLATE_GZIP_BASE64 = (
    "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"
)


@lru_cache(maxsize=1)
def _template() -> dict:
    compressed = base64.b64decode(_TEMPLATE_GZIP_BASE64)
    return json.loads(gzip.decompress(compressed))


def _water_source(profile: WaterProfileResponse) -> dict:
    values = profile.brewfather_values
    calcium = values.calcium
    magnesium = values.magnesium
    sodium = values.sodium
    chloride = values.chloride
    sulfate = values.sulfate
    bicarbonate = values.bicarbonate
    alkalinity = (
        profile.raw_values["alkalinity"].value
        if "alkalinity" in profile.raw_values
        else bicarbonate / 1.22
    )
    cations = calcium / 20.039 + magnesium / 12.1525 + sodium / 22.9898
    anions = chloride / 35.453 + sulfate / 48.03 + bicarbonate / 61.0168
    hardness = calcium * 2.497 + magnesium * 4.118
    residual_alkalinity = alkalinity - calcium / 1.4 - magnesium / 1.7
    generated_at = profile.report.fetched_at
    now_ms = int(generated_at.timestamp() * 1000)
    timestamp = {
        "type": "firestore/timestamp/1.0",
        "seconds": now_ms // 1000,
        "nanoseconds": (now_ms % 1000) * 1_000_000,
    }

    return {
        "magnesium": magnesium,
        "type": "source",
        "ph": values.ph,
        "sodium": sodium,
        "alkalinity": round(alkalinity, 4),
        "residualAlkalinityMeqLCalc": round(residual_alkalinity / 51.4, 5),
        "_timestamp_ms": now_ms,
        "ionBalance": round((cations - anions) / (cations + anions) * 100)
        if cations + anions
        else 0,
        "_timestamp": timestamp,
        "hardness": round(hardness, 2),
        "_version": "3.0.1",
        "_created": timestamp,
        "sulfate": sulfate,
        "calcium": calcium,
        "residualAlkalinity": round(residual_alkalinity, 5),
        "anions": round(anions, 3),
        "bicarbonateMeqL": bicarbonate / 61.0168,
        "_id": uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"mwra-water-{profile.report.report_year}-{profile.report.report_month_number}",
        ).hex[:22],
        "name": f"MWRA Metro-Boston - {profile.report.report_month} {profile.report.report_year}",
        "chloride": chloride,
        "ionBalanceOff": False,
        "soClRatio": round(sulfate / chloride, 2) if chloride else 0,
        "bicarbonate": bicarbonate,
        "hidden": False,
        "cations": round(cations, 3),
    }


def build_brewfather_recipe(profile: WaterProfileResponse) -> dict:
    recipe = copy.deepcopy(_template())
    recipe_name = (
        f"Dummy MWRA {profile.report.report_month} "
        f"{profile.report.report_year} Recipe"
    )
    source = _water_source(profile)
    now = profile.report.fetched_at
    now_ms = int(now.timestamp() * 1000)

    recipe["name"] = recipe_name
    recipe["author"] = ""
    recipe["tags"] = None
    recipe["searchTags"] = []
    recipe["style"] = {
        "name": "Unspecified Ale",
        "category": "Unspecified",
        "categoryNumber": "0",
        "styleLetter": "A",
        "styleGuide": "None",
        "type": "Ale",
        "ogMin": 1.0,
        "ogMax": 1.2,
        "fgMin": 0.99,
        "fgMax": 1.1,
        "ibuMin": 0,
        "ibuMax": 200,
        "colorMin": 0,
        "colorMax": 100,
    }
    recipe_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"mwra-recipe-{profile.report.report_year}-{profile.report.report_month_number}",
    ).hex[:22]
    recipe["_id"] = recipe_id
    recipe["_versionId"] = recipe_id
    recipe["_timestamp_ms"] = now_ms
    recipe["_timestamp"] = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    recipe["_created"] = source["_created"]

    for key in ("source", "mash", "sparge", "total"):
        recipe["water"][key] = copy.deepcopy(source)
    recipe["water"]["meta"]["equalSourceTotal"] = True
    recipe["water"]["mashPh"] = None
    recipe["water"]["mashPhDistilled"] = None
    recipe["water"]["acidPhAdjustment"] = 0
    recipe["water"]["spargeAcidPhAdjustment"] = 0

    return recipe


def brewfather_filename(profile: WaterProfileResponse) -> str:
    month = profile.report.report_month
    year = profile.report.report_year
    return f"Brewfather_RECIPE_Dummy_MWRA_{month}_{year}_Recipe.json"


def _text(parent: ET.Element, tag: str, value: object | None = None) -> ET.Element:
    element = ET.SubElement(parent, tag)
    if value is not None:
        element.text = str(value)
    return element


def _bool(value: object) -> str:
    return "TRUE" if value else "FALSE"


def build_beerxml(recipe: dict) -> bytes:
    root = ET.Element("RECIPES")
    xml_recipe = ET.SubElement(root, "RECIPE")
    _text(xml_recipe, "NAME", recipe["name"])
    _text(xml_recipe, "VERSION", 1)
    _text(xml_recipe, "TYPE", recipe["type"])
    _text(xml_recipe, "NOTES")

    style = ET.SubElement(xml_recipe, "STYLE")
    style_data = recipe["style"]
    _text(style, "NAME", style_data["name"])
    _text(style, "CATEGORY", style_data["category"])
    _text(style, "VERSION", 1)
    _text(style, "CATEGORY_NUMBER", style_data["categoryNumber"])
    _text(style, "STYLE_LETTER", style_data["styleLetter"])
    _text(style, "STYLE_GUIDE", style_data["styleGuide"])
    _text(style, "TYPE", style_data["type"])
    _text(style, "OG_MIN", style_data["ogMin"])
    _text(style, "OG_MAX", style_data["ogMax"])
    _text(style, "FG_MIN", style_data["fgMin"])
    _text(style, "FG_MAX", style_data["fgMax"])
    _text(style, "IBU_MIN", style_data["ibuMin"])
    _text(style, "IBU_MAX", style_data["ibuMax"])
    _text(style, "COLOR_MIN", style_data["colorMin"])
    _text(style, "COLOR_MAX", style_data["colorMax"])

    # Brewfather's BREWER field corresponds to the JSON author. Keep both blank.
    _text(xml_recipe, "BREWER", recipe["author"])
    _text(xml_recipe, "BATCH_SIZE", recipe["batchSize"])
    _text(xml_recipe, "BOIL_SIZE", recipe["boilSize"])
    _text(xml_recipe, "BOIL_TIME", recipe["boilTime"])
    _text(xml_recipe, "EFFICIENCY", recipe["efficiency"])
    _text(xml_recipe, "OG", round(recipe["og"], 3))
    _text(xml_recipe, "FG", recipe["fg"])
    _text(xml_recipe, "CARBONATION", recipe["carbonation"])

    # These record sets are required by BeerXML even when they contain no
    # ingredient records.
    ET.SubElement(xml_recipe, "HOPS")
    fermentables = ET.SubElement(xml_recipe, "FERMENTABLES")
    for item in recipe["fermentables"]:
        fermentable = ET.SubElement(fermentables, "FERMENTABLE")
        _text(fermentable, "NAME", item["name"])
        _text(fermentable, "VERSION", 1)
        _text(fermentable, "TYPE", item["type"])
        _text(fermentable, "AMOUNT", item["amount"])
        _text(fermentable, "YIELD", item["potentialPercentage"])
        _text(fermentable, "COLOR", item["color"])
        _text(fermentable, "ADD_AFTER_BOIL", "FALSE")
        _text(fermentable, "ORIGIN", item.get("origin"))
        _text(fermentable, "SUPPLIER", item.get("supplier"))
        _text(fermentable, "IBU_GAL_PER_LB", item.get("ibuPerAmount") or 0)

    ET.SubElement(xml_recipe, "MISCS")
    ET.SubElement(xml_recipe, "YEASTS")

    # BeerXML supports water profiles even though the supplied Brewfather
    # BeerXML example omitted them. Include one source profile so the export
    # actually carries the selected MWRA chemistry.
    waters = ET.SubElement(xml_recipe, "WATERS")
    source = recipe["water"]["source"]
    water = ET.SubElement(waters, "WATER")
    _text(water, "NAME", source["name"])
    _text(water, "VERSION", 1)
    _text(water, "AMOUNT", recipe["data"]["totalWaterAmount"])
    _text(water, "CALCIUM", source["calcium"])
    _text(water, "MAGNESIUM", source["magnesium"])
    _text(water, "SODIUM", source["sodium"])
    _text(water, "SULFATE", source["sulfate"])
    _text(water, "CHLORIDE", source["chloride"])
    _text(water, "BICARBONATE", source["bicarbonate"])
    _text(water, "PH", source["ph"])
    _text(water, "NOTES")

    mash = ET.SubElement(xml_recipe, "MASH")
    _text(mash, "NAME", recipe["mash"]["name"])
    _text(mash, "VERSION", 1)
    _text(mash, "GRAIN_TEMP", 20)
    mash_steps = ET.SubElement(mash, "MASH_STEPS")
    for item in recipe["mash"]["steps"]:
        step = ET.SubElement(mash_steps, "MASH_STEP")
        _text(step, "NAME", item["type"])
        _text(step, "VERSION", 1)
        _text(step, "TYPE", item["type"])
        _text(step, "STEP_TEMP", item["stepTemp"])
        _text(step, "STEP_TIME", item["stepTime"])
        _text(step, "INFUSE_AMOUNT", recipe["data"]["mashWaterAmount"])

    equipment_data = recipe["equipment"]
    equipment = ET.SubElement(xml_recipe, "EQUIPMENT")
    _text(equipment, "NAME", equipment_data["name"])
    _text(equipment, "VERSION", 1)
    _text(equipment, "BOIL_SIZE", equipment_data["boilSize"])
    _text(equipment, "BATCH_SIZE", equipment_data["batchSize"])
    _text(equipment, "TRUB_CHILLER_LOSS", equipment_data["trubChillerLoss"])
    _text(equipment, "LAUTER_DEADSPACE", equipment_data["mashTunDeadSpace"])
    _text(equipment, "BOIL_TIME", equipment_data["boilTime"])
    _text(equipment, "HOP_UTILIZATION", equipment_data["hopUtilization"] * 100)
    _text(equipment, "EVAP_RATE", equipment_data["evaporationRate"] * 100)
    _text(equipment, "CALC_BOIL_VOLUME", _bool(equipment_data["calcBoilVolume"]))

    fermentation = recipe["fermentation"]
    primary = fermentation["steps"][0]
    _text(xml_recipe, "FERMENTATION_STAGES", len(fermentation["steps"]))
    _text(xml_recipe, "PRIMARY_AGE", primary["stepTime"])
    _text(xml_recipe, "PRIMARY_TEMP", primary["stepTemp"])

    ET.indent(root, space="    ")
    return ET.tostring(root, encoding="ISO-8859-1", xml_declaration=True)


def beerxml_filename(profile: WaterProfileResponse) -> str:
    month = profile.report.report_month
    year = profile.report.report_year
    return f"Brewfather_BeerXML_Dummy_MWRA_{month}_{year}_Recipe.xml"
