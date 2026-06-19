from app.models import BrewfatherValues, RawMeasurement
from app.water_context import build_profile_measurements, measurement_key


def test_configured_fields_are_promoted_and_remaining_fields_are_hidden():
    values = BrewfatherValues(
        calcium=4.37,
        magnesium=0.84,
        sodium=34,
        chloride=27.3,
        sulfate=5.6,
        bicarbonate=49.17,
        pH=9.7,
    )
    other = [
        RawMeasurement(
            parameter="Hardness (2)",
            value=14.4,
            unit="mg/L",
            source_label="fixture",
        ),
        RawMeasurement(
            parameter="Chlorine, Total",
            value=2.1,
            unit="mg/L",
            source_label="fixture",
        ),
    ]

    main, hidden = build_profile_measurements(
        values,
        other,
        ["hardness", "calcium", "ph"],
    )

    assert [item.key for item in main] == ["hardness", "calcium", "ph"]
    assert main[0].unit == "mg/L"
    assert all(item.description for item in main + hidden)
    assert "chlorine_total" in {item.key for item in hidden}
    assert "magnesium" in {item.key for item in hidden}


def test_measurement_keys_ignore_report_footnotes_and_formula_labels():
    assert measurement_key("Alkalinity (3)") == "alkalinity"
    assert measurement_key("Silica (SiO2)") == "silica"
    assert measurement_key("Specific Conductance") == "specific_conductance"
