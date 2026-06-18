const fieldOrder = [
  ["calcium", "Calcium", "ppm"],
  ["magnesium", "Magnesium", "ppm"],
  ["sodium", "Sodium", "ppm"],
  ["chloride", "Chloride", "ppm"],
  ["sulfate", "Sulfate", "ppm"],
  ["bicarbonate", "Bicarbonate", "ppm"],
  ["pH", "pH", ""],
];

const loadingCard = document.querySelector("#loading-card");
const errorCard = document.querySelector("#error-card");
const profileContent = document.querySelector("#profile-content");
const toast = document.querySelector("#toast");
let currentProfile = null;

const formatValue = (value) => Number(value).toFixed(2).replace(/\.?0+$/, "");
const titleCase = (value) => value.charAt(0).toUpperCase() + value.slice(1);

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 2200);
}

function copyText(profile) {
  const values = profile.brewfather_values;
  return [
    `Name: ${profile.name}`,
    ...fieldOrder.map(([key, label, unit]) =>
      `${label}: ${formatValue(values[key])}${unit ? ` ${unit}` : ""}`
    ),
  ].join("\n");
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

function renderProfile(profile) {
  currentProfile = profile;
  document.querySelector("#profile-name").textContent = profile.name;
  document.querySelector("#report-meta").textContent =
    `${profile.report.report_month} ${profile.report.report_year} report · Cached ${new Date(profile.report.fetched_at).toLocaleString()}`;
  document.querySelector("#selected-column").textContent =
    `Selected MWRA column: ${profile.report.selected_column}`;

  const values = profile.brewfather_values;
  document.querySelector("#profile-table").innerHTML = fieldOrder
    .map(([key, label, unit]) => `
      <tr>
        <td>${label}</td>
        <td>${formatValue(values[key])}</td>
        <td>${unit || "—"}</td>
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

async function loadProfile() {
  loadingCard.hidden = false;
  errorCard.hidden = true;
  profileContent.hidden = true;
  try {
    const response = await fetch("/api/latest", { headers: { Accept: "application/json" } });
    const payload = await response.json();
    if (!response.ok) throw payload;
    renderProfile(payload);
  } catch (error) {
    renderError(error instanceof Error ? { message: error.message } : error);
  }
}

document.querySelector("#copy-button").addEventListener("click", async () => {
  if (!currentProfile) return;
  const copied = await writeClipboard(copyText(currentProfile));
  showToast(copied ? "Brewfather values copied" : "Clipboard access was unavailable");
});

document.querySelector("#retry-button").addEventListener("click", loadProfile);

document.querySelectorAll("details").forEach((details) => {
  details.addEventListener("toggle", () => {
    if (!details.open) return;
    const iframe = details.querySelector("iframe[data-src]");
    if (iframe && !iframe.src) iframe.src = iframe.dataset.src;
  });
});

loadProfile();
