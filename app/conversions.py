from app.errors import ReportParseError
from app.models import BrewfatherValues, Conversion, RawMeasurement

FIELD_SOURCES = {
    "calcium": "calcium",
    "magnesium": "magnesium",
    "sodium": "sodium",
    "chloride": "chloride",
    "sulfate": "sulfate",
    "pH": "ph",
}


def to_ppm(value: float, unit: str) -> tuple[float, str]:
    normalized = (
        unit.lower()
        .replace("μ", "u")
        .replace("µ", "u")
        .replace(" ", "")
        .replace("liter", "l")
    )
    if normalized in {"mg/l", "mg/l.", "ppm"}:
        return value, "1 mg/L = 1 ppm"
    if normalized in {"ug/l", "ug/l."}:
        return value / 1000, "ug/L ÷ 1000 = ppm"
    raise ReportParseError(f"Unsupported MWRA measurement unit: {unit!r}")


def convert_measurements(
    raw: dict[str, RawMeasurement],
) -> tuple[BrewfatherValues, list[Conversion]]:
    required = set(FIELD_SOURCES.values()) | {"alkalinity"}
    missing = sorted(required - set(raw))
    if missing:
        raise ReportParseError(
            "The report is missing required values: " + ", ".join(missing) + "."
        )

    values: dict[str, float] = {}
    conversions: list[Conversion] = []

    for field, source_key in FIELD_SOURCES.items():
        measurement = raw[source_key]
        if field == "pH":
            result = measurement.value
            formula = "No conversion"
            result_unit = ""
        else:
            result, formula = to_ppm(measurement.value, measurement.unit)
            result_unit = "ppm"
        result = round(result, 2)
        values[field] = result
        conversions.append(
            Conversion(
                field=field,
                source_parameter=measurement.parameter,
                source_value=measurement.value,
                source_unit=measurement.unit,
                formula=formula,
                result=result,
                result_unit=result_unit,
            )
        )

    alkalinity = raw["alkalinity"]
    alkalinity_ppm, base_formula = to_ppm(alkalinity.value, alkalinity.unit)
    bicarbonate = round(alkalinity_ppm * 1.22, 2)
    values["bicarbonate"] = bicarbonate
    conversions.insert(
        5,
        Conversion(
            field="bicarbonate",
            source_parameter=alkalinity.parameter,
            source_value=alkalinity.value,
            source_unit=alkalinity.unit,
            formula=f"{base_formula}; alkalinity as CaCO3 × 1.22",
            result=bicarbonate,
            result_unit="ppm",
        ),
    )

    return BrewfatherValues.model_validate(values), conversions
