from pathlib import Path

from app.parser import parse_report_pdf

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
