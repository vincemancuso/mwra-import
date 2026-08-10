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


def test_history_chart_ui_is_present():
    script = (PROJECT_ROOT / "static" / "app.js").read_text()
    styles = (PROJECT_ROOT / "static" / "styles.css").read_text()
    template = (PROJECT_ROOT / "templates" / "index.html").read_text()

    assert "/api/history" in script
    assert "activeHistoryKeys" in script
    assert "relativeChange" in script
    assert "maxAbsChange" in script
    assert "minimum ±10% range" in script
    assert "history-chart" in script
    assert "history-controls" in script
    assert "Brewing values over time" in template
    assert "relative change" in template
    assert ".history-toggle" in styles
    assert ".chart-line" in styles
    assert ".chart-point" in styles
    assert "chartShapes" in script
    assert "pointSymbolPath" in script
    assert "historyLegendSymbol" in script
    assert "chartTooltip" in script
    assert ".history-symbol" in styles
    assert ".chart-line-hit" in styles
    assert ".chart-series:hover" in styles
    assert ".chart-series:has(.chart-point-wrap:hover)" in styles
