from pathlib import Path
import tomllib

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


DEFAULT_MWRA_REPORTS_PAGE_URL = (
    "https://www.mwra.com/your-water-system/drinking-water-quality/"
    "monthly-water-quality-test-results"
)
DEFAULT_MAIN_PROFILE_FIELDS = [
    "calcium",
    "magnesium",
    "sodium",
    "chloride",
    "sulfate",
    "bicarbonate",
    "ph",
]


class AppSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    mwra_reports_page_url: HttpUrl = HttpUrl(DEFAULT_MWRA_REPORTS_PAGE_URL)
    main_profile_fields: list[str] = Field(
        default_factory=lambda: list(DEFAULT_MAIN_PROFILE_FIELDS)
    )

    @field_validator("main_profile_fields")
    @classmethod
    def validate_main_profile_fields(cls, fields: list[str]) -> list[str]:
        normalized = [field.strip().lower() for field in fields if field.strip()]
        if not normalized:
            raise ValueError("main_profile_fields must contain at least one field")
        if len(normalized) != len(set(normalized)):
            raise ValueError("main_profile_fields cannot contain duplicates")
        return normalized


def load_settings(path: Path) -> AppSettings:
    if not path.exists():
        raise RuntimeError(
            f"Application configuration file is missing: {path}. "
            "Restore app-config.toml in the project root."
        )
    try:
        with path.open("rb") as config_file:
            data = tomllib.load(config_file)
        return AppSettings.model_validate(data)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        raise RuntimeError(f"Could not load application configuration {path}: {exc}") from exc
