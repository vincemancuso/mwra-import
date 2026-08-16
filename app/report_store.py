import csv
import re
from collections.abc import Iterable
from pathlib import Path

from app.models import RawMeasurement

BASE_COLUMNS = ["key", "parameter", "unit", "source_label"]


def month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


class RawValueStore:
    """CSV-backed store for parsed MWRA treated-water raw measurements.

    The CSV is intentionally simple and human-editable:

    key,parameter,unit,source_label,2026-01,2026-02,...

    Each month column contains the raw value exactly as parsed from MWRA. Brewing
    unit conversions are still performed by the app at response/render time.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def exists(self) -> bool:
        return self.path.exists() and self.path.stat().st_size > 0

    def month_columns(self) -> list[str]:
        header, _ = self._read_rows()
        return [column for column in header if column not in BASE_COLUMNS]

    def sorted_month_columns(self) -> list[str]:
        return sorted(
            column
            for column in self.month_columns()
            if re.fullmatch(r"20\d{2}-(?:0[1-9]|1[0-2])", column)
        )

    def export_rows(self) -> tuple[list[str], list[dict[str, str]]]:
        """Return the stored raw CSV header and rows for download/export use."""
        return self._read_rows()

    def has_month(self, year: int, month: int) -> bool:
        return month_key(year, month) in self.month_columns()

    def load_month(self, year: int, month: int) -> dict[str, RawMeasurement]:
        key = month_key(year, month)
        header, rows = self._read_rows()
        if key not in header:
            return {}

        measurements: dict[str, RawMeasurement] = {}
        for row in rows:
            value = (row.get(key) or "").strip()
            if value == "":
                continue
            measurements[row["key"]] = RawMeasurement(
                parameter=row.get("parameter") or row["key"].replace("_", " ").title(),
                value=float(value),
                unit=row.get("unit") or "mg/L",
                source_label=(
                    row.get("source_label") or "Metro-Boston treated/finished water"
                ),
            )
        return measurements

    def save_month(
        self,
        year: int,
        month: int,
        measurements: dict[str, RawMeasurement],
    ) -> None:
        month = month_key(year, month)
        header, rows = self._read_rows()
        months = sorted({column for column in header if column not in BASE_COLUMNS} | {month})
        row_by_key = {row["key"]: row for row in rows if row.get("key")}

        for key, measurement in sorted(measurements.items()):
            row = row_by_key.setdefault(
                key,
                {
                    "key": key,
                    "parameter": measurement.parameter,
                    "unit": measurement.unit,
                    "source_label": measurement.source_label,
                },
            )
            row["parameter"] = row.get("parameter") or measurement.parameter
            row["unit"] = row.get("unit") or measurement.unit
            row["source_label"] = row.get("source_label") or measurement.source_label
            row[month] = f"{measurement.value:g}"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [*BASE_COLUMNS, *months]
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for key in sorted(row_by_key):
                row = {field: row_by_key[key].get(field, "") for field in fieldnames}
                writer.writerow(row)

    def _read_rows(self) -> tuple[list[str], list[dict[str, str]]]:
        if not self.exists():
            return [*BASE_COLUMNS], []
        with self.path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or BASE_COLUMNS)
            rows = list(reader)
        for column in BASE_COLUMNS:
            if column not in header:
                header.append(column)
        return header, rows


def merge_measurements(
    raw_values: dict[str, RawMeasurement],
    other_values: Iterable[tuple[str, RawMeasurement]],
) -> dict[str, RawMeasurement]:
    merged = dict(raw_values)
    for key, measurement in other_values:
        merged.setdefault(key, measurement)
    return merged
