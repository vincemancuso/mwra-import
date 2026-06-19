import re

from app.models import BrewfatherValues, ProfileMeasurement, RawMeasurement


FIELD_LABELS = {
    "ph": "pH",
    "bicarbonate": "Bicarbonate",
    "chlorine_total": "Chlorine, Total",
    "ammonia_n_total": "Ammonia-N, Total",
    "nitrate_n": "Nitrate-N",
    "silica": "Silica (SiO2)",
    "uv_254": "UV-254",
}

FIELD_CONTEXT = {
    "calcium": (
        "Calcium contributes hardness, can help lower mash pH through malt "
        "phosphate reactions, and supports wort clarification and yeast flocculation."
    ),
    "magnesium": (
        "Magnesium contributes hardness and is a yeast nutrient. Malt normally "
        "supplies enough; elevated brewing-water levels can taste bitter or astringent."
    ),
    "sodium": (
        "Modest sodium can round and accentuate beer flavor, especially with "
        "chloride. High levels may taste salty or become harsh with high sulfate."
    ),
    "chloride": (
        "Chloride can emphasize fullness, sweetness, and a softer palate. It is "
        "the chloride ion, not chlorine disinfectant."
    ),
    "sulfate": (
        "Sulfate can make hop bitterness seem sharper and the finish drier. High "
        "sulfate combined with high chloride or sodium may taste harsh or minerally."
    ),
    "bicarbonate": (
        "Bicarbonate is the main alkaline buffer in most drinking water. It can "
        "raise mash pH; pale grists often need less, while dark acidic grists may need more."
    ),
    "ph": (
        "This is the source-water pH, not mash pH. It has limited predictive value "
        "by itself; alkalinity and the grain bill have a larger effect on mash pH."
    ),
    "alkalinity": (
        "Alkalinity measures the water's acid-neutralizing capacity. It strongly "
        "influences mash and sparge pH and how much acid treatment may be required."
    ),
    "hardness": (
        "Hardness mainly reflects calcium and magnesium. It is not inherently bad "
        "for brewing; its balance with alkalinity is more useful than hardness alone."
    ),
    "chlorine_total": (
        "Total chlorine represents free chlorine plus chloramine-type residuals. "
        "Brewers normally remove them to avoid medicinal or plastic-like chlorophenols."
    ),
    "iron": (
        "Iron is not a brewing-water target. Even small amounts can taste metallic "
        "and can accelerate oxidative staling reactions."
    ),
    "manganese": (
        "Manganese is not normally adjusted for brewing. Elevated amounts can add "
        "metallic flavor and are generally undesirable in brewing liquor."
    ),
    "nitrate_n": (
        "Nitrate-N is primarily a source-water quality indicator, not a flavor ion. "
        "Elevated nitrate can be reduced to nitrite, which is harmful to yeast."
    ),
    "nitrite": (
        "Nitrite is undesirable in brewing water because very low concentrations "
        "can inhibit or harm yeast; it can also indicate a water-quality problem."
    ),
    "ammonia_n_total": (
        "Ammonia is a nitrogen indicator rather than a normal brewing adjustment. "
        "In chlorinated water it may be associated with chloramine formation."
    ),
    "potassium": (
        "Malt already contributes substantial potassium to wort. Water potassium "
        "is rarely adjusted; elevated levels may taste salty or affect mash enzymes."
    ),
    "fluoride": (
        "Fluoride is monitored for drinking-water treatment and has no routine role "
        "in brewing-water adjustment at typical municipal concentrations."
    ),
    "barium": (
        "Barium is a trace drinking-water contaminant measurement, not a brewing "
        "mineral target. Brewers generally do not adjust it independently."
    ),
    "bromide": (
        "Bromide has no routine brewing role. It is mainly monitored as a source-water "
        "constituent and as a potential precursor to treatment by-products."
    ),
    "color": (
        "Water color is an aesthetic and treatment indicator that can reflect "
        "dissolved organic matter or metals. It is separate from beer color from malt."
    ),
    "orthophosphate": (
        "Orthophosphate may be added for corrosion control. It is not a standard "
        "brewing target and can interact with calcium in water and wort."
    ),
    "silica": (
        "Silica is not normally adjusted in brewing water. At elevated process pH, "
        "silicate extraction is associated with harsher wort and beer character."
    ),
    "specific_conductance": (
        "Specific conductance is a broad measure of dissolved ionic material. It "
        "cannot reveal which flavor-active ions are present."
    ),
    "total_dissolved_solids": (
        "Total dissolved solids summarizes overall mineralization. It is useful for "
        "tracking consistency but does not replace an ion-by-ion water profile."
    ),
    "total_organic_carbon": (
        "Total organic carbon is a treatment and source-water quality indicator. It "
        "is not a recipe adjustment target but can relate to taste, odor, and by-products."
    ),
    "total_phosphorus": (
        "Total phosphorus is a broad water-quality measurement. Malt contributes far "
        "more brewing-relevant phosphate, so this is not normally adjusted from tap water."
    ),
    "uv_254": (
        "UV-254 absorbance is a treatment indicator for light-absorbing organic matter. "
        "It is not a direct brewing-water adjustment value."
    ),
}


def measurement_key(name: str) -> str:
    normalized = name.lower()
    normalized = re.sub(r"\([^)]*\)", " ", normalized)
    normalized = normalized.replace("sulphate", "sulfate")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    aliases = {
        "chlorine_total": "chlorine_total",
        "total_chlorine": "chlorine_total",
        "hardness_2": "hardness",
        "alkalinity_3": "alkalinity",
        "ph_3": "ph",
        "silica_sio2": "silica",
    }
    return aliases.get(normalized, normalized)


def context_for(key: str, label: str) -> str:
    return FIELD_CONTEXT.get(
        key,
        (
            f"{label} is reported by MWRA as a treated-water quality measurement. "
            "It is not commonly used as a direct homebrewing water adjustment target."
        ),
    )


def build_profile_measurements(
    values: BrewfatherValues,
    other_values: list[RawMeasurement],
    main_fields: list[str],
) -> tuple[list[ProfileMeasurement], list[ProfileMeasurement]]:
    standard_units = {
        "calcium": "ppm",
        "magnesium": "ppm",
        "sodium": "ppm",
        "chloride": "ppm",
        "sulfate": "ppm",
        "bicarbonate": "ppm",
        "ph": "",
    }
    available: dict[str, ProfileMeasurement] = {}
    dumped_values = values.model_dump(by_alias=False)
    for key, unit in standard_units.items():
        label = FIELD_LABELS.get(key, key.title())
        available[key] = ProfileMeasurement(
            key=key,
            label=label,
            value=dumped_values[key],
            unit=unit,
            description=context_for(key, label),
        )

    for measurement in other_values:
        key = measurement_key(measurement.parameter)
        if key in available:
            continue
        label = FIELD_LABELS.get(key, measurement.parameter)
        available[key] = ProfileMeasurement(
            key=key,
            label=label,
            value=measurement.value,
            unit=measurement.unit,
            description=context_for(key, label),
        )

    main = [available.pop(key) for key in main_fields if key in available]
    other = sorted(available.values(), key=lambda item: item.label.lower())
    return main, other
