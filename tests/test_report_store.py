from app.models import RawMeasurement
from app.report_store import RawValueStore


def test_raw_value_store_writes_months_as_columns_and_preserves_units(tmp_path):
    store = RawValueStore(tmp_path / "mwra-values.csv")

    store.save_month(
        2026,
        4,
        {
            "calcium": RawMeasurement(
                parameter="Calcium",
                value=4370,
                unit="UG/L",
                source_label="Metro-Boston treated/finished water",
            ),
            "ph": RawMeasurement(
                parameter="pH",
                value=9.7,
                unit="standard units",
                source_label="Metro-Boston treated/finished water",
            ),
        },
    )
    store.save_month(
        2026,
        5,
        {
            "calcium": RawMeasurement(
                parameter="Calcium",
                value=4320,
                unit="UG/L",
                source_label="Metro-Boston treated/finished water",
            )
        },
    )

    csv_text = store.path.read_text(encoding="utf-8")
    assert csv_text.splitlines()[0] == "key,parameter,unit,source_label,2026-04,2026-05"
    assert "calcium,Calcium,UG/L,Metro-Boston treated/finished water,4370,4320" in csv_text

    april = store.load_month(2026, 4)
    assert april["calcium"].value == 4370
    assert april["calcium"].unit == "UG/L"
    assert april["ph"].value == 9.7
