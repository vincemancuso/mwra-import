from pathlib import Path

APP_NAME = "MWRA Brewfather Water Profile"
MWRA_MONTHLY_URL = (
    "https://www.mwra.com/your-water-system/drinking-water-quality/"
    "monthly-water-quality-test-results"
)
MWRA_BASE_URL = "https://www.mwra.com"
DEFAULT_COLUMN = (
    "Wachusett System / Metro-Boston / Carroll Water TP Finished Water Tap / Treated"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

HTTP_TIMEOUT_SECONDS = 30.0
USER_AGENT = f"{APP_NAME}/0.1 (local personal-use application)"
