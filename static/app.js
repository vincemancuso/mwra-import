const loadingCard = document.querySelector("#loading-card");
const errorCard = document.querySelector("#error-card");
const profileContent = document.querySelector("#profile-content");
const reportSelect = document.querySelector("#report-select");
const toast = document.querySelector("#toast");
let currentProfile = null;
let currentPreviousProfile = null;
let latestReportKey = null;
let reportCatalog = [];
let profileRequestId = 0;
let historyData = null;
const expandedHistoryRows = new Set();

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
const brewingScales = {
  calcium: { min: 0, max: 200, targetMin: 50, targetMax: 150, note: "Palmer/AHA commonly cite 50–150/200 ppm as a useful brewing calcium range." },
  magnesium: { min: 0, max: 50, targetMin: 10, targetMax: 30, note: "Common brewing guidance puts magnesium around 10–30 ppm, with high levels becoming bitter/astringent." },
  sodium: { min: 0, max: 200, targetMin: 0, targetMax: 100, note: "Sodium can round malt character at modest levels; high levels can taste salty or harsh." },
  chloride: { min: 0, max: 250, targetMin: 50, targetMax: 150, note: "Chloride often supports fullness and malt roundness; very high levels can become excessive." },
  sulfate: { min: 0, max: 400, targetMin: 50, targetMax: 250, note: "Sulfate emphasizes dryness and hop bitterness; very high levels can seem harsh." },
  bicarbonate: { min: 0, max: 250, targetMin: 0, targetMax: 120, note: "Bicarbonate/alkalinity is grist-dependent; lower values generally suit pale beers, higher values can suit darker acidic grists." },
  ph: { min: 5, max: 10.5, targetMin: 6.5, targetMax: 8.5, note: "Source-water pH is less important than alkalinity and mash pH; the band is a drinking-water-style reference, not a mash target." },
};

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

function historySeriesFor(key) {
  if (!historyData?.series) return null;
  const index = historyData.series.findIndex((series) => series.key === key);
  if (index < 0) return null;
  return { series: historyData.series[index], index };
}

function rangeIndicator(measurement) {
  const historyMatch = historySeriesFor(measurement.key);
  const scale = fixedScaleFor(historyMatch?.series || {
    key: measurement.key,
    max_value: measurement.value,
  });
  const tooltipId = `range-${measurement.key.replaceAll("_", "-")}-tip`;
  let symbol = "—";
  let state = "unavailable";
  let label = `No brewing reference range for ${measurement.label}`;
  let rangeText = "Not configured";
  let currentText = formatChartValue(measurement.value, measurement.unit);
  let meaningText = "No broad brewing reference band is configured for this value.";

  if (scale.targetMin !== null && scale.targetMax !== null) {
    rangeText = `${formatChartValue(scale.targetMin, measurement.unit)}–${formatChartValue(scale.targetMax, measurement.unit)}`;
    if (measurement.value < scale.targetMin) {
      symbol = "▼";
      state = "outside";
      label = `${measurement.label} is below the broad brewing reference range`;
      meaningText = "Below the broad brewing reference band.";
    } else if (measurement.value > scale.targetMax) {
      symbol = "▲";
      state = "outside";
      label = `${measurement.label} is above the broad brewing reference range`;
      meaningText = "Above the broad brewing reference band.";
    } else {
      symbol = "—";
      state = "within";
      label = `${measurement.label} is within the broad brewing reference range`;
      meaningText = "Within the broad brewing reference band.";
    }
  }

  return `
    <span class="trend-help">
      <button class="trend-indicator range-${state}" type="button"
        aria-label="${escapeHtml(label)}"
        aria-describedby="${tooltipId}">${symbol}</button>
      <span class="trend-tip-content" id="${tooltipId}" role="tooltip">
        <strong>${escapeHtml(measurement.label)} brewing range</strong>
        <span class="trend-tip-row">
          <span>Current value</span>
          <b>${escapeHtml(currentText)}</b>
        </span>
        <span class="trend-tip-row">
          <span>Reference band</span>
          <b>${escapeHtml(rangeText)}</b>
        </span>
        <span class="trend-tip-row">
          <span>Status</span>
          <b>${escapeHtml(meaningText)}</b>
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
  currentPreviousProfile = previousProfile;
  const reportKey = `${profile.report.report_year}-${String(profile.report.report_month_number || "").padStart(2, "0")}`;
  reportSelect.value = reportKey;
  document.querySelector("#profile-name").textContent = profile.name;
  document.querySelector("#report-meta").textContent =
    `${profile.report.report_month} ${profile.report.report_year} report${reportKey === latestReportKey ? " · Latest available" : ""} · Cached ${new Date(profile.report.fetched_at).toLocaleString()}`;
  document.querySelector("#selected-column").textContent =
    `Selected MWRA column: ${profile.report.selected_column}`;

  document.querySelector("#profile-table").innerHTML = profile.profile_values
    .map((measurement) => {
      const isExpanded = expandedHistoryRows.has(measurement.key);
      const historyMatch = historySeriesFor(measurement.key);
      return `
        <tr class="profile-value-row${isExpanded ? " is-expanded" : ""}">
          <td class="history-toggle-cell">
            <button class="history-toggle-button" type="button"
              data-history-toggle="${escapeHtml(measurement.key)}"
              aria-label="${escapeHtml(`${isExpanded ? "Hide" : "Show"} historical context for ${measurement.label}`)}"
              aria-expanded="${isExpanded ? "true" : "false"}"
              aria-controls="history-row-${escapeHtml(measurement.key)}">
              <span aria-hidden="true"></span>
            </button>
          </td>
          <td>
            ${measurementHelp(measurement, "main")}
          </td>
          <td>
            <button class="value-copy-button" type="button"
              data-copy-value="${escapeHtml(formatValue(measurement.value))}"
              data-copy-label="${escapeHtml(measurement.label)}"
              aria-label="${escapeHtml(`Copy ${measurement.label} value`)}">
              ${formatValue(measurement.value)}
            </button>
          </td>
          <td>${escapeHtml(measurement.unit) || "—"}</td>
          <td class="trend-cell">${rangeIndicator(measurement)}</td>
          <td class="trend-cell">${trendIndicator(measurement, previousProfile)}</td>
        </tr>
        <tr class="history-context-row" id="history-row-${escapeHtml(measurement.key)}"${isExpanded ? "" : " hidden"}>
          <td colspan="6">${historyContext(measurement, historyMatch)}</td>
        </tr>`;
    })
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

function fixedScaleFor(series) {
  return brewingScales[series.key] || {
    min: 0,
    max: Math.max(1, Math.ceil(series.max_value * 1.25)),
    targetMin: null,
    targetMax: null,
    note: "This field uses a fallback fixed scale because no brewing-reference scale is configured.",
  };
}

function chartPath(series, scale, width, height, padding) {
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const valueRange = scale.max - scale.min || 1;
  const xFor = (pointIndex) =>
    padding.left + (series.points.length <= 1 ? plotWidth / 2 : (pointIndex / (series.points.length - 1)) * plotWidth);
  const yFor = (value) => {
    const clamped = Math.min(scale.max, Math.max(scale.min, value));
    return padding.top + (1 - ((clamped - scale.min) / valueRange)) * plotHeight;
  };
  return {
    points: series.points.map((point, index) => ({
      ...point,
      x: xFor(index),
      y: yFor(point.value),
    })),
    yFor,
  };
}

function expandedChart(series, index) {
  const scale = fixedScaleFor(series);
  const width = 820;
  const height = 280;
  const padding = { top: 22, right: 82, bottom: 52, left: 76 };
  const { points, yFor } = chartPath(series, scale, width, height, padding);
  const path = points
    .map((point, pointIndex) => `${pointIndex === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");
  const xLabelEvery = Math.max(1, Math.ceil(points.length / 6));
  const valueTicks = [scale.max, (scale.max + scale.min) / 2, scale.min];
  const gridLines = valueTicks
    .map((tick) => `
      <line class="chart-grid" x1="${padding.left}" y1="${yFor(tick)}" x2="${width - padding.right}" y2="${yFor(tick)}"></line>
      <text class="chart-y-label" x="${padding.left - 10}" y="${yFor(tick) + 4}">${formatChartValue(tick, series.unit)}</text>`)
    .join("");
  const targetBand = scale.targetMin !== null && scale.targetMax !== null
    ? `<rect class="chart-target-band" x="${padding.left}" y="${yFor(scale.targetMax)}" width="${width - padding.left - padding.right}" height="${Math.max(2, yFor(scale.targetMin) - yFor(scale.targetMax))}"></rect>`
    : "";
  const pointMarks = points
    .map((point) => `
      <g class="chart-point-wrap" tabindex="0" role="img"
        aria-label="${escapeHtml(`${series.label}, ${point.month_year}: ${formatChartValue(point.value, series.unit)}`)}">
        <g class="chart-point" fill="${historyColor(index)}" stroke="${historyColor(index)}">
          ${pointSymbolPath(historyShape(index), point.x, point.y)}
        </g>
        ${chartTooltip(point.x, point.y, [
          series.label,
          `${point.month_year}`,
          `${formatChartValue(point.value, series.unit)}`,
        ], "point-tooltip")}
      </g>`)
    .join("");
  const xLabels = points
    .map((point, pointIndex) => {
      if (pointIndex !== 0 && pointIndex !== points.length - 1 && pointIndex % xLabelEvery !== 0) return "";
      const shortMonth = point.report_month.slice(0, 3);
      return `
        <line class="chart-tick" x1="${point.x}" y1="${height - padding.bottom}" x2="${point.x}" y2="${height - padding.bottom + 6}"></line>
        <text class="chart-x-label" x="${point.x}" y="${height - padding.bottom + 24}">${shortMonth} ${point.report_year}</text>`;
    })
    .join("");
  return `
    <div class="expanded-chart-wrap">
      <svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(`${series.label} historical chart`)}">
        <rect class="chart-bg" x="0" y="0" width="${width}" height="${height}" rx="14"></rect>
        ${targetBand}
        ${gridLines}
        <line class="chart-axis" x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}"></line>
        <line class="chart-axis" x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}"></line>
        ${xLabels}
        <path class="chart-line" d="${path}" stroke="${historyColor(index)}"></path>
        ${pointMarks}
      </svg>
    </div>`;
}

function historyContext(measurement, historyMatch) {
  if (!historyMatch) {
    return `
      <div class="history-inline-empty">
        Historical context is loading or unavailable for ${escapeHtml(measurement.label)}.
      </div>`;
  }

  const { series, index } = historyMatch;
  const scale = fixedScaleFor(series);
  const targetText = scale.targetMin !== null && scale.targetMax !== null
    ? `${formatChartValue(scale.targetMin, series.unit)}–${formatChartValue(scale.targetMax, series.unit)}`
    : "Reference band unavailable";
  return `
      <div class="history-inline">
        <div class="history-inline-heading">
          <span class="history-card-symbol">${historyLegendSymbol(index)}</span>
          <div>
            <strong>${escapeHtml(series.label)} historical context</strong>
            <p>Fixed brewing-reference scale, not a data-fitted axis.</p>
          </div>
        </div>
        <div class="history-summary">
          <span><b>Historical MWRA range</b>${formatChartValue(series.min_value, series.unit)} → ${formatChartValue(series.max_value, series.unit)}</span>
          <span><b>Chart scale</b>${formatChartValue(scale.min, series.unit)} → ${formatChartValue(scale.max, series.unit)}</span>
          <span class="reference-summary"><b>Brewing reference</b>${escapeHtml(targetText)}</span>
        </div>
        ${expandedChart(series, index)}
        <p class="history-note">${escapeHtml(scale.note)}</p>
      </div>`;
}

async function loadHistory() {
  try {
    historyData = await fetchJson("/api/history");
    if (currentProfile) {
      renderProfile(currentProfile, currentPreviousProfile);
    }
  } catch (error) {
    console.error("Historical report data could not be loaded.", error);
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

document.querySelector("#profile-table").addEventListener("click", (event) => {
  const valueButton = event.target.closest("[data-copy-value]");
  if (valueButton) {
    const label = valueButton.dataset.copyLabel || "Value";
    writeClipboard(valueButton.dataset.copyValue || "").then((copied) => {
      showToast(copied ? `${label} copied` : "Clipboard access was unavailable");
    });
    return;
  }

  const button = event.target.closest("[data-history-toggle]");
  if (!button) return;
  const key = button.dataset.historyToggle;
  if (expandedHistoryRows.has(key)) {
    expandedHistoryRows.delete(key);
  } else {
    expandedHistoryRows.add(key);
  }
  if (currentProfile) renderProfile(currentProfile, currentPreviousProfile);
});

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
