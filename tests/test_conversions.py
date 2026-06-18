import pytest

from app.conversions import convert_measurements, to_ppm
from app.models import RawMeasurement


def measurement(parameter: str, value: float, unit: str) -> RawMeasurement:
    return RawMeasurement(
        parameter=parameter,
        value=value,
        unit=unit,
        source_label="fixture treated water",
    )


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [(27.3, "MG/L", 27.3), (4370, "UG/L", 4.37), (845, "µg/L", 0.845)],
)
def test_to_ppm(value: float, unit: str, expected: float):
    assert to_ppm(value, unit)[0] == pytest.approx(expected)


def test_brewfather_conversion_math():
    raw = {
        "calcium": measurement("Calcium", 4370, "UG/L"),
        "magnesium": measurement("Magnesium", 845, "UG/L"),
        "sodium": measurement("Sodium", 34, "MG/L"),
        "chloride": measurement("Chloride", 27.3, "MG/L"),
        "sulfate": measurement("Sulfate (SO4)", 5.6, "MG/L"),
        "alkalinity": measurement("Alkalinity as CaCO3", 40.3, "MG/L"),
        "ph": measurement("pH", 9.7, "S.U."),
    }

    profile, conversions = convert_measurements(raw)

    assert profile.calcium == 4.37
    assert profile.magnesium == 0.84
    assert profile.sodium == 34
    assert profile.chloride == 27.3
    assert profile.sulfate == 5.6
    assert profile.bicarbonate == 49.17
    assert profile.ph == 9.7
    bicarbonate = next(item for item in conversions if item.field == "bicarbonate")
    assert "1.22" in bicarbonate.formula
