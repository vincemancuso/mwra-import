"""Delete and rebuild the local MWRA CSV database and cached report PDFs.

Run from the project root after installing the app dependencies:

    python refresh_local_data.py
"""

from __future__ import annotations

import asyncio

from clear_local_data import (
    RAW_VALUES_CSV,
    REPORTS_DIR,
    cached_pdfs,
    cached_report_months,
    linked_report_months,
)

CONFIRMATION = "REFRESH MWRA DATA"


def load_app_dependencies():
    try:
        from app.config import CONFIG_PATH
        from app.report_store import RawValueStore
        from app.service import WaterProfileService
        from app.settings import load_settings
    except ModuleNotFoundError as exc:
        missing = exc.name or "an application dependency"
        print(f"Cannot rebuild the cache because {missing!r} is not installed.")
        print()
        print("Activate the virtual environment and install the app first:")
        print()
        print("  source .venv/bin/activate")
        print("  python -m pip install -e .")
        print()
        print("No local data was removed.")
        return None

    return CONFIG_PATH, RawValueStore, WaterProfileService, load_settings


def delete_local_data() -> None:
    if RAW_VALUES_CSV.exists():
        RAW_VALUES_CSV.unlink()
        print(f"Deleted {RAW_VALUES_CSV}")
    else:
        print("No CSV database found.")

    for pdf in cached_pdfs():
        pdf.unlink()
        print(f"Deleted {pdf}")


async def main() -> int:
    csv_months = cached_report_months()
    pdfs = cached_pdfs()
    linked_months = linked_report_months()

    print("WARNING: this will permanently remove and rebuild local MWRA cached data.")
    print()
    print(f"CSV database: {RAW_VALUES_CSV}")
    print(f"Cached PDF directory: {REPORTS_DIR}")
    print(f"CSV month columns found: {len(csv_months)}")
    print(f"Cached PDFs found: {len(pdfs)}")
    print()
    print(
        "If MWRA no longer publishes one of these reports, deleted values may "
        "not be recoverable from the MWRA website."
    )

    if linked_months is None:
        print(
            "Because the MWRA website could not be checked, refreshing cannot "
            "continue safely."
        )
        return 1

    unavailable = sorted(csv_months - linked_months)
    if unavailable:
        print()
        print("Cached CSV months not currently linked on the MWRA page:")
        for month in unavailable:
            print(f"  - {month}")
        print("Refreshing now may permanently remove those local values.")
    else:
        print("All cached CSV months are currently linked on the MWRA page.")

    dependencies = load_app_dependencies()
    if dependencies is None:
        return 1
    config_path, raw_value_store, service_class, load_settings = dependencies

    print()
    entered = input(f'Type "{CONFIRMATION}" to continue: ')
    if entered != CONFIRMATION:
        print("Canceled. No local data was removed.")
        return 1

    delete_local_data()

    print()
    print("Rebuilding local MWRA cache from currently linked reports...")
    service = service_class(load_settings(config_path))
    catalog = await service.reports(force_refresh=True)
    rebuilt_months = raw_value_store(RAW_VALUES_CSV).month_columns()
    print(f"Reports linked on MWRA page: {len(catalog.reports)}")
    print(f"CSV month columns rebuilt: {len(rebuilt_months)}")
    print(f"Cached PDFs rebuilt: {len(cached_pdfs())}")

    if service._store_errors:
        print()
        print("Some linked reports could not be cached:")
        for report_month, error in sorted(service._store_errors.items()):
            print(f"  - {report_month}: {error}")
        return 1

    print("Done. Local MWRA data has been freshly rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
