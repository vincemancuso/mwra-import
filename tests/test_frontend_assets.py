from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def test_main_profile_trend_ui_is_present():
    script = (PROJECT_ROOT / "static" / "app.js").read_text()
    styles = (PROJECT_ROOT / "static" / "styles.css").read_text()

    assert 'symbol = "▲"' in script
    assert 'symbol = "▼"' in script
    assert 'symbol = "—"' in script
    assert "Previous report" in script
    assert "Previous value" in script
    assert "Change" in script
    assert "previousReport = selectedIndex" in script
    assert ".trend-tip-content" in styles
    assert ".trend-tip-row" in styles
    assert ".trend-help:focus-within" in styles
    assert ".trend-down" in styles
    assert ".trend-steady" in styles
    assert "measurement-label-trigger" in script
    assert ".measurement-tip-content > strong" in styles
