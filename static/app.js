const loadingCard = document.querySelector("#loading-card");
const errorCard = document.querySelector("#error-card");
const profileContent = document.querySelector("#profile-content");
const reportSelect = document.querySelector("#report-select");
const toast = document.querySelector("#toast");
let currentProfile = null;
let latestReportKey = null;
let reportCatalog = [];
let profileRequestId = 0;
let historyData = null;
let activeHistoryKeys = new Set();

const chartColors = [
  "#a7193f",
  "#4f6726",
  "#9a6615",
  "#355f7d",
  "#5b4a3e",
  "#c04f2a",
  "#6f5aa7",
];
const chartShapes = ["circle", "square", "diamond", "triangle", "pentagon", "hexagon", "cross"];

const formatValue = (value) => Number(value).toFixed(2).replace(/\.?0+$/, "");
const titleCase = (value) => value.charAt(0).toUpperCase() + value.slice(1);
const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");
const historyPointKey = (point) =>
  `${point.report_year}-${String(point.report_month_number).padStart(2, "0")}`;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 2200);
}

function copyText(profile) {
  return [
    `Name: ${profile.name}`,
    ...profile.profile_values.map((measurement) =>
      `${measurement.label}: ${formatValue(measurement.value)}${measurement.unit ? ` ${measurement.unit}` : ""}`
    ),
  ].join("\n");
}

function measurementHelp(measurement, idPrefix) {
  const tooltipId = `${idPrefix}-${measurement.key.replaceAll("_", "-")}-tip`;
  return `
    <span class="measurement-help">
      <button class="measurement-label-trigger" type="button"
        aria-label="About ${escapeHtml(measurement.label)}"
        aria-describedby="${tooltipId}">${escapeHtml(measurement.label)}</button>
      <span class="measurement-tip-content" id="${tooltipId}" role="tooltip">
        <strong>${escapeHtml(measurement.label)}</strong>
        <span>${escapeHtml(measurement.description)}</span>
      </span>
    </span>`;
}

function comparisonValue(profile, key) {
  if (!profile) return null;
  return [...(profile.profile_values || []), ...(profile.other_values || [])]
    .find((measurement) => measurement.key === key) || null;
}

function trendIndicator(measurement, previousProfile) {
  const previous = comparisonValue(previousProfile, measurement.key);
  const tooltipId = `trend-${measurement.key.replaceAll("_", "-")}-tip`;
  const currentValue = Number(formatValue(measurement.value));

  let symbol = "—";
  let state = "steady";
  let label = `${measurement.label} is steady`;
  let previousMonth = "Previous report";
  let previousValueText = "Not available";
  let changeText = "No comparison available";

  if (!previousProfile) {
    state = "unavailable";
    label = `No previous report comparison for ${measurement.label}`;
    previousMonth = "Earlier report";
    changeText = "No earlier linked MWRA report";
  } else if (!previous) {
    state = "unavailable";
    label = `No previous value for ${measurement.label}`;
    previousMonth = `${previousProfile.report.report_month} ${previousProfile.report.report_year}`;
    changeText = "Measurement not reported";
  } else {
    const previousValue = Number(formatValue(previous.value));
    const delta = Number((currentValue - previousValue).toFixed(2));
    const unit = measurement.unit ? ` ${measurement.unit}` : "";

    previousMonth = `${previousProfile.report.report_month} ${previousProfile.report.report_year}`;
    previousValueText = `${formatValue(previous.value)}${unit}`;
    changeText = `${delta > 0 ? "+" : ""}${formatValue(delta)}${unit}`;
    if (delta > 0) {
      symbol = "▲";
      state = "up";
      label = `${measurement.label} increased since the previous report`;
    } else if (delta < 0) {
      symbol = "▼";
      state = "down";
      label = `${measurement.label} decreased since the previous report`;
    }
  }

  return `
    <span class="trend-help">
      <button class="trend-indicator trend-${state}" type="button"
        aria-label="${escapeHtml(label)}"
        aria-describedby="${tooltipId}">${symbol}</button>
      <span class="trend-tip-content" id="${tooltipId}" role="tooltip">
        <strong>${escapeHtml(measurement.label)} comparison</strong>
        <span class="trend-tip-row">
          <span>Previous report</span>
          <b>${escapeHtml(previousMonth)}</b>
        </span>
        <span class="trend-tip-row">
          <span>Previous value</span>
          <b>${escapeHtml(previousValueText)}</b>
        </span>
        <span class="trend-tip-row">
          <span>Change</span>
          <b>${escapeHtml(changeText)}</b>
        </span>
      </span>
    </span>`;
}

async function writeClipboard(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fall through to the local, permission-free selection method.
    }
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  return copied;
}

function renderProfile(profile, previousProfile = null) {
  currentProfile = profile;
  const reportKey = `${profile.report.report_year}-${String(profile.report.report_month_number || "").padStart(2, "0")}`;
  reportSelect.value = reportKey;
  document.querySelector("#profile-name").textContent = profile.name;
  document.querySelector("#report-meta").textContent =
    `${profile.report.report_month} ${profile.report.report_year} report${reportKey === latestReportKey ? " · Latest available" : ""} · Cached ${new Date(profile.report.fetched_at).toLocaleString()}`;
  document.querySelector("#selected-column").textContent =
    `Selected MWRA column: ${profile.report.selected_column}`;

  document.querySelector("#profile-table").innerHTML = profile.profile_values
    .map((measurement) => `
      <tr>
        <td>
          ${measurementHelp(measurement, "main")}
        </td>
        <td>${formatValue(measurement.value)}</td>
        <td>${escapeHtml(measurement.unit) || "—"}</td>
        <td class="trend-cell">${trendIndicator(measurement, previousProfile)}</td>
      </tr>`)
    .join("");

  document.querySelector("#conversion-table").innerHTML = profile.conversions
    .map((conversion) => `
      <tr>
        <td>${titleCase(conversion.field)}</td>
        <td>${conversion.source_parameter}</td>
        <td>${formatValue(conversion.source_value)} ${conversion.source_unit}</td>
        <td>${conversion.formula}</td>
        <td>${formatValue(conversion.result)} ${conversion.result_unit}</td>
      </tr>`)
    .join("");

  const otherValues = profile.other_values || [];
  document.querySelector("#other-values").innerHTML = otherValues.length
    ? otherValues
      .map((measurement) => `
        <div class="stat-item">
          <span class="stat-label">
            ${measurementHelp(measurement, "other")}
          </span>
          <span class="stat-value">${formatValue(measurement.value)} ${escapeHtml(measurement.unit)}</span>
        </div>`)
      .join("")
    : '<p class="muted">No additional numeric measurements were found in this report.</p>';

  const pdfUrl = `/api/reports/${profile.report.report_year}/${profile.report.report_month_number}/pdf`;
  const brewfatherUrl = `/api/reports/${profile.report.report_year}/${profile.report.report_month_number}/brewfather.json`;
  const beerxmlUrl = `/api/reports/${profile.report.report_year}/${profile.report.report_month_number}/beerxml.xml`;
  const pdfLink = document.querySelector("#pdf-link");
  const pdfFrame = document.querySelector("#pdf-frame");
  document.querySelector("#brewfather-download").href = brewfatherUrl;
  document.querySelector("#beerxml-download").href = beerxmlUrl;
  pdfLink.href = pdfUrl;
  pdfFrame.dataset.src = pdfUrl;
  if (pdfFrame.closest("details").open) {
    pdfFrame.src = pdfUrl;
  } else {
    pdfFrame.removeAttribute("src");
  }

  reportSelect.disabled = false;
  loadingCard.hidden = true;
  errorCard.hidden = true;
  profileContent.hidden = false;
}

function renderError(payload) {
  loadingCard.hidden = true;
  profileContent.hidden = true;
  errorCard.hidden = false;
  document.querySelector("#error-title").textContent =
    payload.error ? payload.error.replace(/([A-Z])/g, " $1").trim() : "The latest report could not be loaded.";
  document.querySelector("#error-message").textContent =
    payload.message || payload.detail || "An unexpected error occurred.";
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  const payload = await response.json();
  if (!response.ok) throw payload;
  return payload;
}

function formatChartValue(value, unit = "") {
  return `${formatValue(value)}${unit ? ` ${unit}` : ""}`;
}

function formatPercent(value) {
  const percent = value * 100;
  return `${percent > 0 ? "+" : ""}${formatValue(percent)}%`;
}

function historyColor(index) {
  return chartColors[index % chartColors.length];
}

function historyShape(index) {
  return chartShapes[index % chartShapes.length];
}

function chartTooltip(x, y, lines, className = "") {
  const width = 184;
  const height = 34 + Math.max(0, lines.length - 1) * 16;
  const tooltipX = Math.max(112, Math.min(900 - width - 14, x + 12));
  const tooltipY = Math.max(12, y - height - 14);
  const text = lines
    .map((line, index) => `
      <text class="chart-tooltip-${index === 0 ? "title" : "text"}" x="${tooltipX + 12}" y="${tooltipY + 20 + index * 16}">${escapeHtml(line)}</text>`)
    .join("");
  return `
    <g class="chart-tooltip ${className}" aria-hidden="true">
      <rect x="${tooltipX}" y="${tooltipY}" width="${width}" height="${height}" rx="8"></rect>
      ${text}
    </g>`;
}

function pointSymbolPath(shape, x, y, size = 5.5) {
  const points = {
    square: [
      [x - size, y - size],
      [x + size, y - size],
      [x + size, y + size],
      [x - size, y + size],
    ],
    diamond: [
      [x, y - size - 1],
      [x + size + 1, y],
      [x, y + size + 1],
      [x - size - 1, y],
    ],
    triangle: [
      [x, y - size - 1],
      [x + size + 1, y + size],
      [x - size - 1, y + size],
    ],
    pentagon: Array.from({ length: 5 }, (_, index) => {
      const angle = -Math.PI / 2 + (index * 2 * Math.PI) / 5;
      return [x + Math.cos(angle) * (size + 1), y + Math.sin(angle) * (size + 1)];
    }),
    hexagon: Array.from({ length: 6 }, (_, index) => {
      const angle = Math.PI / 6 + (index * 2 * Math.PI) / 6;
      return [x + Math.cos(angle) * (size + 1), y + Math.sin(angle) * (size + 1)];
    }),
  };
  if (shape === "cross") {
    return `
      <path class="symbol-cross" d="M ${x - size} ${y} L ${x + size} ${y} M ${x} ${y - size} L ${x} ${y + size}"></path>`;
  }
  const shapePoints = points[shape];
  if (!shapePoints) {
    return `<circle cx="${x}" cy="${y}" r="${size}"></circle>`;
  }
  const path = shapePoints
    .map(([pointX, pointY], index) => `${index === 0 ? "M" : "L"} ${pointX} ${pointY}`)
    .join(" ");
  return `<path d="${path} Z"></path>`;
}

function historyLegendSymbol(index) {
  const color = historyColor(index);
  const shape = historyShape(index);
  return `
    <svg class="history-symbol" viewBox="0 0 24 24" aria-hidden="true">
      <g style="--symbol-color: ${color}" fill="${color}" stroke="${color}">
        ${pointSymbolPath(shape, 12, 12, shape === "cross" ? 7.5 : 6.3)}
      </g>
    </svg>`;
}

function renderHistoryControls() {
  const controls = document.querySelector("#history-controls");
  controls.innerHTML = historyData.series
    .map((series, index) => {
      const checked = activeHistoryKeys.has(series.key) ? " checked" : "";
      return `
        <label class="history-toggle">
          <input type="checkbox" value="${escapeHtml(series.key)}"${checked}>
          ${historyLegendSymbol(index)}
          <span>
            <strong>${escapeHtml(series.label)}</strong>
            <small>${formatChartValue(series.min_value, series.unit)} → ${formatChartValue(series.max_value, series.unit)}</small>
          </span>
        </label>`;
    })
    .join("");

  controls.querySelectorAll("input").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) {
        activeHistoryKeys.add(input.value);
      } else {
        activeHistoryKeys.delete(input.value);
      }
      renderHistoryChart();
    });
  });
}

function renderHistoryChart() {
  const svg = document.querySelector("#history-chart");
  if (!historyData?.series?.length) return;

  const visibleSeries = historyData.series
    .map((series, index) => ({
      ...series,
      color: historyColor(index),
      shape: historyShape(index),
    }))
    .filter((series) => activeHistoryKeys.has(series.key));

  const width = 900;
  const height = 360;
  const padding = { top: 26, right: 92, bottom: 58, left: 104 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const allPoints = historyData.series.flatMap((series) => series.points);
  const monthLabels = [...new Map(allPoints.map((point) => [historyPointKey(point), point])).values()];
  const xFor = (point) => {
    const index = monthLabels.findIndex((label) => historyPointKey(label) === historyPointKey(point));
    return padding.left + (monthLabels.length <= 1 ? plotWidth / 2 : (index / (monthLabels.length - 1)) * plotWidth);
  };
  const labelEvery = Math.max(1, Math.ceil(monthLabels.length / 7));
  const plottedSeries = visibleSeries.map((series) => {
    const baseline = series.points[0]?.value || 0;
    return {
      ...series,
      baseline,
      points: series.points.map((point) => ({
        ...point,
        relativeChange: baseline === 0
          ? point.value - baseline
          : (point.value - baseline) / Math.abs(baseline),
      })),
    };
  });
  const relativeValues = plottedSeries.flatMap((series) =>
    series.points.map((point) => point.relativeChange)
  );
  const maxAbsChange = Math.max(
    0.1,
    ...relativeValues.map((value) => Math.abs(value))
  ) * 1.08;
  const yFor = (relativeChange) =>
    padding.top + ((maxAbsChange - relativeChange) / (maxAbsChange * 2)) * plotHeight;

  const gridLines = [maxAbsChange, maxAbsChange / 2, 0, -maxAbsChange / 2, -maxAbsChange]
    .map((tick) => {
      const y = yFor(tick);
      const label = tick === 0 ? "Baseline" : formatPercent(tick);
      return `
        <line class="chart-grid" x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}"></line>
        <text class="chart-y-label" x="${padding.left - 10}" y="${y + 4}">${label}</text>`;
    })
    .join("");

  const xLabels = monthLabels
    .map((point, index) => {
      if (
        index !== 0 &&
        index !== monthLabels.length - 1 &&
        index % labelEvery !== 0
      ) {
        return "";
      }
      const x = xFor(point);
      const shortMonth = point.report_month.slice(0, 3);
      return `
        <line class="chart-tick" x1="${x}" y1="${height - padding.bottom}" x2="${x}" y2="${height - padding.bottom + 6}"></line>
        <text class="chart-x-label" x="${x}" y="${height - padding.bottom + 24}">${shortMonth} ${point.report_year}</text>`;
    })
    .join("");

  const lines = plottedSeries
    .map((series) => {
      const plottedPoints = series.points.map((point) => ({
        ...point,
        x: xFor(point),
        y: yFor(point.relativeChange),
      }));
      const path = series.points
        .map((point, index) => {
          const command = index === 0 ? "M" : "L";
          return `${command} ${xFor(point).toFixed(2)} ${yFor(point.relativeChange).toFixed(2)}`;
        })
        .join(" ");
      const labelPoint = plottedPoints[Math.floor(plottedPoints.length / 2)] || plottedPoints[0];
      const points = plottedPoints
        .map((point) => `
          <g class="chart-point-wrap" tabindex="0" role="img"
            aria-label="${escapeHtml(`${series.label}, ${point.month_year}: ${formatChartValue(point.value, series.unit)}`)}">
            <g class="chart-point" fill="${series.color}" stroke="${series.color}">
              ${pointSymbolPath(series.shape, point.x, point.y)}
            </g>
            ${chartTooltip(point.x, point.y, [
              series.label,
              `${point.month_year}`,
              `${formatChartValue(point.value, series.unit)}`,
              `${formatPercent(point.relativeChange)} from first report`,
            ], "point-tooltip")}
          </g>`)
        .join("");
      return `
        <g class="chart-series" tabindex="0" role="img"
          aria-label="${escapeHtml(`${series.label} trend, ${formatChartValue(series.min_value, series.unit)} to ${formatChartValue(series.max_value, series.unit)}`)}">
          <path class="chart-line-hit" d="${path}"></path>
          <path class="chart-line" d="${path}" stroke="${series.color}"></path>
          ${points}
          ${chartTooltip(labelPoint?.x || padding.left, labelPoint?.y || padding.top, [
            `${series.label} trend`,
            `First report: ${formatChartValue(series.baseline, series.unit)}`,
            `Range: ${formatChartValue(series.min_value, series.unit)} → ${formatChartValue(series.max_value, series.unit)}`,
          ], "series-tooltip")}
        </g>`;
    })
    .join("");

  const emptyState = visibleSeries.length
    ? ""
    : `<text class="chart-empty" x="${width / 2}" y="${height / 2}">Select at least one value to show the trend chart.</text>`;

  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.innerHTML = `
    <rect class="chart-bg" x="0" y="0" width="${width}" height="${height}" rx="14"></rect>
    ${gridLines}
    <line class="chart-axis" x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}"></line>
    <line class="chart-axis" x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}"></line>
    ${xLabels}
    ${lines}
    ${emptyState}`;

  const skipped = historyData.skipped_reports?.length
    ? ` ${historyData.skipped_reports.length} linked report${historyData.skipped_reports.length === 1 ? "" : "s"} could not be parsed and were skipped.`
    : "";
  document.querySelector("#history-caption").textContent =
    `Lines show percent change from each field's first available report. The vertical scale recalculates whenever selected values change, with a minimum ±10% range so nearly flat values still look nearly flat.${skipped}`;
}

async function loadHistory() {
  const status = document.querySelector("#history-status");
  const content = document.querySelector("#history-content");
  status.hidden = false;
  status.textContent = "Loading historical report data…";
  content.hidden = true;
  try {
    historyData = await fetchJson("/api/history");
    activeHistoryKeys = new Set(historyData.series.map((series) => series.key));
    if (!historyData.series.length) {
      status.textContent = "No historical brewing values were available to chart.";
      return;
    }
    renderHistoryControls();
    renderHistoryChart();
    status.hidden = true;
    content.hidden = false;
  } catch (error) {
    const message = error?.message || error?.detail || "Historical report data could not be loaded.";
    status.textContent = message;
  }
}

async function loadProfile(year, month, initial = false) {
  const requestId = ++profileRequestId;
  loadingCard.hidden = false;
  errorCard.hidden = true;
  reportSelect.disabled = true;
  if (initial) profileContent.hidden = true;
  try {
    const selectedIndex = reportCatalog.findIndex(
      (report) => report.year === year && report.month === month
    );
    const previousReport = selectedIndex >= 0
      ? reportCatalog[selectedIndex + 1]
      : null;
    const [payload, previousProfile] = await Promise.all([
      fetchJson(`/api/reports/${year}/${month}`),
      previousReport
        ? fetchJson(`/api/reports/${previousReport.year}/${previousReport.month}`)
          .catch(() => null)
        : Promise.resolve(null),
    ]);
    if (requestId !== profileRequestId) return;
    renderProfile(payload, previousProfile);
  } catch (error) {
    if (requestId !== profileRequestId) return;
    renderError(error instanceof Error ? { message: error.message } : error);
  }
}

async function initialize() {
  try {
    const catalog = await fetchJson("/api/reports");
    reportCatalog = catalog.reports;
    latestReportKey = `${catalog.latest.year}-${String(catalog.latest.month).padStart(2, "0")}`;
    reportSelect.innerHTML = catalog.reports
      .map((report) => {
        const key = `${report.year}-${String(report.month).padStart(2, "0")}`;
        return `<option value="${key}">${report.month_year}${key === latestReportKey ? " (latest)" : ""}</option>`;
      })
      .join("");
    reportSelect.value = latestReportKey;
    await loadProfile(catalog.latest.year, catalog.latest.month, true);
    loadHistory();
  } catch (error) {
    renderError(error instanceof Error ? { message: error.message } : error);
  }
}

document.querySelector("#copy-button").addEventListener("click", async () => {
  if (!currentProfile) return;
  const copied = await writeClipboard(copyText(currentProfile));
  showToast(copied ? "Water profile values copied" : "Clipboard access was unavailable");
});

document.querySelector("#retry-button").addEventListener("click", initialize);

reportSelect.addEventListener("change", () => {
  const [year, month] = reportSelect.value.split("-").map(Number);
  loadProfile(year, month);
});

document.querySelectorAll("details").forEach((details) => {
  details.addEventListener("toggle", () => {
    if (!details.open) return;
    const iframe = details.querySelector("iframe[data-src]");
    if (iframe && !iframe.src) iframe.src = iframe.dataset.src;
  });
});

initialize();
