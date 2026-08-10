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


def test_table_values_can_be_copied_individually():
    script = (PROJECT_ROOT / "static" / "app.js").read_text()
    styles = (PROJECT_ROOT / "static" / "styles.css").read_text()
    template = (PROJECT_ROOT / "templates" / "index.html").read_text()

    assert "data-copy-value" in script
    assert "data-copy-label" in script
    assert "Copy ${measurement.label} value" in script
    assert "${label} copied" in script
    assert ".value-copy-button" in styles
    assert "brewersfriend-import" not in script
    assert "Brewer" not in template


def test_history_chart_ui_is_present():
    script = (PROJECT_ROOT / "static" / "app.js").read_text()
    styles = (PROJECT_ROOT / "static" / "styles.css").read_text()
    template = (PROJECT_ROOT / "templates" / "index.html").read_text()

    assert "/api/history" in script
    assert "brewingScales" in script
    assert "fixedScaleFor" in script
    assert "expandedChart" in script
    assert "history-chart" in script
    assert "historyContext" in script
    assert "rangeIndicator" in script
    assert "data-history-toggle" in script
    assert "expandedHistoryRows" in script
    assert "Current MWRA Water Profile" in template
    assert "Brewing range" in template
    assert ".history-toggle-button" in styles
    assert ".history-inline" in styles
    assert "reference-summary" in script
    assert ".history-summary .reference-summary" in styles
    assert ".range-outside" in styles
    assert ".range-within" in styles
    assert ".chart-target-band" in styles
    assert ".chart-line" in styles
    assert ".chart-point" in styles
    assert "chartShapes" in script
    assert "pointSymbolPath" in script
    assert "historyLegendSymbol" in script
    assert "chartTooltip" in script
    assert ".history-symbol" in styles
