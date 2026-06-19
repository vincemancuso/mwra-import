const loadingCard = document.querySelector("#loading-card");
const errorCard = document.querySelector("#error-card");
const profileContent = document.querySelector("#profile-content");
const reportSelect = document.querySelector("#report-select");
const toast = document.querySelector("#toast");
let currentProfile = null;
let latestReportKey = null;
let reportCatalog = [];
let profileRequestId = 0;

const formatValue = (value) => Number(value).toFixed(2).replace(/\.?0+$/, "");
const titleCase = (value) => value.charAt(0).toUpperCase() + value.slice(1);
const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

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
