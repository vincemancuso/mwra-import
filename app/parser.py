import re
from collections.abc import Iterable
from pathlib import Path

import pdfplumber

from app.errors import ReportParseError
from app.models import RawMeasurement

PARAMETER_ALIASES = {
    "calcium": ("calcium",),
    "magnesium": ("magnesium",),
    "sodium": ("sodium",),
    "chloride": ("chloride",),
    "sulfate": ("sulfate", "sulphate"),
    "alkalinity": ("alkalinity",),
    "ph": ("ph",),
}
BREWFATHER_PARAMETER_KEYS = {"calcium", "magnesium", "sodium", "chloride", "sulfate", "ph"}
UNIT_PATTERN = re.compile(
    r"(mg\s*/\s*l|[uμµ]g\s*/\s*l|ppm|\bstandard units?\b|(?<![A-Za-z])s\.?u\.?(?![A-Za-z]))",
    re.I,
)
NUMBER_PATTERN = re.compile(r"(?<![\w.])(?:<\s*)?(-?\d+(?:\.\d+)?)")


def _clean(value: object) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def _parameter_key(text: str) -> str | None:
    normalized = re.sub(r"[^a-z]+", " ", text.lower()).strip()
    for key, aliases in PARAMETER_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases):
            return key
    return None


def _unit_from_text(text: str, key: str) -> str:
    if key == "ph":
        return "standard units"
    match = UNIT_PATTERN.search(text)
    return _clean(match.group(1)) if match else "mg/L"


def _numeric_cells(cells: Iterable[str]) -> list[float]:
    values: list[float] = []
    for cell in cells:
        cleaned = _clean(cell).replace(",", "")
        if re.fullmatch(r"(?:<\s*)?-?\d+(?:\.\d+)?", cleaned):
            values.append(float(cleaned.replace("<", "").strip()))
    return values


def _from_tables(pdf: pdfplumber.PDF) -> dict[str, RawMeasurement]:
    found: dict[str, RawMeasurement] = {}
    for page in pdf.pages:
        for table in page.extract_tables() or []:
            rows = [[_clean(cell) for cell in row] for row in table if row]
            if not rows:
                continue
            header_text = " | ".join(" ".join(row) for row in rows[:6]).lower()
            treated_indexes = [
                index
                for row in rows[:6]
                for index, cell in enumerate(row)
                if any(
                    token in cell.lower()
                    for token in ("carroll", "metro-boston", "finished", "treated")
                )
            ]
            preferred_index = max(treated_indexes) if treated_indexes else None

            for row in rows:
                row_text = " | ".join(row)
                key = _parameter_key(row[0] if row else row_text)
                if not key:
                    continue
                unit = _unit_from_text(row_text, key)
                value: float | None = None
                if preferred_index is not None and preferred_index < len(row):
                    candidates = _numeric_cells([row[preferred_index]])
                    value = candidates[0] if candidates else None
                if value is None:
                    candidates = _numeric_cells(row[1:])
                    if candidates:
                        # MWRA places treated/finished water to the right of source water.
                        value = candidates[-1]
                if value is not None:
                    found[key] = RawMeasurement(
                        parameter=row[0] or key.title(),
                        value=value,
                        unit=unit,
                        source_label="Metro-Boston treated/finished water",
                    )
    return found


def _other_treated_values(pdf: pdfplumber.PDF) -> list[RawMeasurement]:
    found: dict[str, RawMeasurement] = {}
    for page in pdf.pages:
        for table in page.extract_tables() or []:
            rows = [[_clean(cell) for cell in row] for row in table if row]
            if not rows:
                continue
            header = rows[0]
            treated_indexes = [
                index
                for index, cell in enumerate(header)
                if any(
                    token in cell.lower()
                    for token in ("carroll", "metro-boston", "finished", "treated")
                )
            ]
            unit_indexes = [
                index for index, cell in enumerate(header) if cell.lower() == "units"
            ]
            if not treated_indexes:
                continue
            treated_index = max(treated_indexes)
            unit_index = unit_indexes[0] if unit_indexes else None

            for row in rows[1:]:
                if treated_index >= len(row):
                    continue
                parameter = row[0].strip()
                if not parameter:
                    continue
                key = _parameter_key(parameter)
                if key in BREWFATHER_PARAMETER_KEYS:
                    continue
                candidates = _numeric_cells([row[treated_index]])
                if not candidates:
                    continue
                unit = (
                    row[unit_index]
                    if unit_index is not None and unit_index < len(row) and row[unit_index]
                    else _unit_from_text(" | ".join(row), key or "")
                )
                normalized_name = re.sub(r"\s+", " ", parameter).strip()
                found[normalized_name.lower()] = RawMeasurement(
                    parameter=normalized_name,
                    value=candidates[0],
                    unit=unit,
                    source_label="Metro-Boston treated/finished water",
                )
    return list(found.values())


def _from_lines(pdf: pdfplumber.PDF) -> dict[str, RawMeasurement]:
    found: dict[str, RawMeasurement] = {}
    for page in pdf.pages:
        text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
        lower = text.lower()
        if not any(word in lower for word in ("mineral", "calcium", "alkalinity")):
            continue
        for line in text.splitlines():
            key = _parameter_key(line)
            if not key:
                continue
            unit = _unit_from_text(line, key)
            without_unit = UNIT_PATTERN.sub(" ", line)
            numbers = [float(value) for value in NUMBER_PATTERN.findall(without_unit)]
            if numbers:
                found[key] = RawMeasurement(
                    parameter=_clean(line).split(str(numbers[0]))[0].strip(" :-") or key.title(),
                    value=numbers[-1],
                    unit=unit,
                    source_label="Metro-Boston treated/finished water",
                )
    return found


def parse_report_pdf_details(
    path: Path,
) -> tuple[dict[str, RawMeasurement], list[RawMeasurement]]:
    try:
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                raise ReportParseError("The downloaded MWRA PDF contains no pages.")
            values = _from_tables(pdf)
            fallback = _from_lines(pdf)
            for key, measurement in fallback.items():
                values.setdefault(key, measurement)
            other_values = _other_treated_values(pdf)
    except ReportParseError:
        raise
    except Exception as exc:
        raise ReportParseError(f"The MWRA PDF could not be read: {exc}") from exc

    missing = sorted(set(PARAMETER_ALIASES) - set(values))
    if missing:
        raise ReportParseError(
            "Could not extract all required Metro-Boston treated-water values "
            f"from the MWRA PDF. Missing: {', '.join(missing)}. "
            "MWRA may have changed the report layout. A local PDF upload fallback "
            "is planned for a future version."
        )
    return values, other_values


def parse_report_pdf(path: Path) -> dict[str, RawMeasurement]:
    values, _ = parse_report_pdf_details(path)
    return values
