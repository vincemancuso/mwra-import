from pathlib import Path

APP_NAME = "MWRA Homebrewing Water Profile"
MWRA_BASE_URL = "https://www.mwra.com"
DEFAULT_COLUMN = (
    "Wachusett System / Metro-Boston / Carroll Water TP Finished Water Tap / Treated"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "app-config.toml"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
RAW_VALUES_CSV = PROJECT_ROOT / "data" / "mwra-treated-water-values.csv"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

HTTP_TIMEOUT_SECONDS = 30.0
USER_AGENT = f"{APP_NAME}/0.1 (local personal-use application)"
