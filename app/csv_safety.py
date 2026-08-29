CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def safe_csv_cell(value: object) -> object:
    """Prefix spreadsheet-formula-looking text without changing numeric values."""
    if not isinstance(value, str):
        return value
    if value.startswith(("\t", "\r", "\n")):
        return f"'{value}"
    stripped = value.lstrip()
    if stripped and stripped[0] in CSV_FORMULA_PREFIXES:
        return f"'{value}"
    return value


def safe_csv_row(row: dict[str, object]) -> dict[str, object]:
    return {key: safe_csv_cell(value) for key, value in row.items()}
