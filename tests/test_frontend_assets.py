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


def test_profile_table_has_unit_toggle_and_inline_other_metrics():
    script = (PROJECT_ROOT / "static" / "app.js").read_text()
    styles = (PROJECT_ROOT / "static" / "styles.css").read_text()
    template = (PROJECT_ROOT / "templates" / "index.html").read_text()

    assert "data-unit-mode" in script
    assert "currentUnitMode" in script
    assert "displayMeasurement" in script
    assert "conversionFor" in script
    assert "Brewing-ready values converted for water calculators" in template
    assert "Original MWRA report values and units before brewing conversions" in template
    assert "unit-tip-content" in template
    assert "aria-describedby=\"brewing-units-tip\"" in template
    assert "aria-describedby=\"mwra-units-tip\"" in template
    assert "data-other-metrics-toggle" in script
    assert "otherMetricsExpanded" in script
    assert "other-metric-row" in script
    assert "Brewing units" in template
    assert "MWRA units" in template
    assert "Other metrics" in script
    assert "export-menu" in template
    assert "Show export download options" in template
    assert "brewfather-download" in template
    assert "beerxml-download" in template
    assert "conversion-table" not in template
    assert "other-values" not in template
    assert ".unit-toggle" in styles
    assert ".unit-tip-content" in styles
    assert ".unit-toggle-help:focus-within" in styles
    assert ".table-toolbar" in styles
    assert ".export-menu-panel" in styles
    assert ".other-metrics-toggle" in styles


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
    assert "currentReportPointKey" in script
    assert "selectedPoint" in script
    assert "chart-selected-line" in script
    assert ".chart-selected-line" in styles
    assert ".chart-selected-point" in styles
    assert "formatSeriesValue" in script
    assert "pH units are logarithmic" in script
    assert "26% change in hydrogen ion activity" in script
    assert "data-history-toggle" in script
    assert "expandedHistoryRows" in script
    assert "Treated MWRA Water Profile" in template
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
    assert "historyIntervalOptions" in script
    assert "3 months" in script
    assert "Year to date" in script
    assert "All time" in script
    assert "data-history-interval" in script
    assert "visibleSeriesFor" in script
    assert "chartLinePaths" in script
    assert ".history-interval-toggle" in styles
    assert ".history-interval-button.active" in styles
