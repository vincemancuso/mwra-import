from pathlib import Path

from app.parser import parse_report_pdf, parse_report_pdf_details

FIXTURES = Path(__file__).parent / "fixtures"


def test_extracts_metro_boston_treated_column_from_fixture_pdf():
    values = parse_report_pdf(FIXTURES / "mwra-report.pdf")

    assert values["alkalinity"].value == 40.3
    assert values["calcium"].value == 4370
    assert values["calcium"].unit.upper() == "UG/L"
    assert values["magnesium"].value == 845
    assert values["sodium"].value == 34
    assert values["chloride"].value == 27.3
    assert values["sulfate"].value == 5.6
    assert values["ph"].value == 9.7


def test_extracts_other_numeric_treated_water_values():
    _, other = parse_report_pdf_details(FIXTURES / "mwra-report.pdf")
    values = {item.parameter: item for item in other}

    assert values["Alkalinity (3)"].value == 40.3
    assert values["Hardness (2)"].value == 14.4
    assert values["Fluoride"].value == 0.72
    assert values["Potassium"].value == 935
    assert values["Potassium"].unit == "UG/L"
