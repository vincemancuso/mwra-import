from pathlib import Path

import pytest

from app.settings import load_settings


def test_loads_admin_configuration(tmp_path: Path):
    config_path = tmp_path / "app-config.toml"
    config_path.write_text(
        """
mwra_reports_page_url = "https://example.test/monthly-reports"
main_profile_fields = ["hardness", "calcium", "ph"]
""".strip()
    )

    settings = load_settings(config_path)

    assert str(settings.mwra_reports_page_url) == "https://example.test/monthly-reports"
    assert settings.main_profile_fields == ["hardness", "calcium", "ph"]


def test_rejects_empty_main_field_list(tmp_path: Path):
    config_path = tmp_path / "app-config.toml"
    config_path.write_text(
        """
mwra_reports_page_url = "https://example.test/monthly-reports"
main_profile_fields = []
""".strip()
    )

    with pytest.raises(RuntimeError, match="at least one field"):
        load_settings(config_path)
