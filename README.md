<p align="center">
  <img src="static/wort-water-mark.png" alt="Boston Wort Processors hop and water emblem" width="140">
</p>

<h1 align="center">MWRA Homebrewing Water Profile</h1>

<p align="center">
  <strong>Boston Wort Processors Present</strong><br>
  A brewing-water utility for members of Boston's homebrew community.
</p>

<p align="center">
  <a href="http://www.wort.org"><strong>Learn more about the Boston Wort Processors at wort.org</strong></a>
</p>

A small local web app that finds the latest
[MWRA monthly water-quality report](https://www.mwra.com/your-water-system/drinking-water-quality/monthly-water-quality-test-results),
extracts the Metro-Boston treated-water mineral analysis, and formats the
results as a practical homebrewing water profile. Use the displayed values
with the brewing water calculator or recipe software of your choice.

Brewfather is supported as an optional destination through recipe JSON and
BeerXML downloads, but this is not a Brewfather-specific tool and does not
require a Brewfather account.

> [!IMPORTANT]
> **This project is vibecoded.** The initial application, parser, interface,
> tests, and documentation were produced through an AI-assisted conversation
> with OpenAI Codex, directed and reviewed by the repository owner. It has been
> tested against fixtures and a live MWRA report, but it should not be treated
> as professionally audited water-chemistry or production software. See
> [AI_DISCLOSURE.md](AI_DISCLOSURE.md) for the full disclosure.

## About the Boston Wort Processors

The [Boston Wort Processors](http://www.wort.org) are a Boston-area homebrew
club founded in 1984. The club brings brewers together through meetings,
education, competitions, shared resources, and community events.

Visit [wort.org](http://www.wort.org) to learn about the club, membership,
upcoming events, educational resources, and homebrewing activities.

## What it does

- Finds the newest linked monthly report on the MWRA website.
- Lists every monthly report currently linked on that page and lets you switch
  between them, defaulting to the newest one.
- Downloads and caches the source PDF in `data/reports/`.
- Stores parsed raw treated-water measurements in a local CSV cache so normal
  page loads do not repeatedly download or parse the same MWRA PDFs.
- Extracts the `Carroll Water TP Fin. Water Tap (Treated)` values.
- Converts MWRA units into standard brewing-water values in ppm.
- Displays calcium, magnesium, sodium, chloride, sulfate, bicarbonate, and pH.
- Adds brewing-reference status indicators to the main profile table and lets
  each value expand into a historical single-value chart on a fixed
  brewing-reference scale.
- Expands to show the other numeric Carroll finished-water measurements found
  in the same MWRA report.
- Copies a ready-to-paste text profile to the clipboard.
- Compares each main profile value with the previous linked report using
  up, down, or steady indicators with exact prior values on hover or focus.
- Shows the raw MWRA measurements and conversion formulas.
- Embeds the original cached PDF for easy verification.

## Historical context charts

The historical context rows are intentionally conservative. They do **not**
stretch each chart to the minimum and maximum MWRA values, because that can
make stable municipal water look more volatile than it is. Instead, each
brewing value uses a fixed, broad brewing-reference scale:

| Field | Chart scale |
| --- | --- |
| Calcium | 0–200 ppm |
| Magnesium | 0–50 ppm |
| Sodium | 0–200 ppm |
| Chloride | 0–250 ppm |
| Sulfate | 0–400 ppm |
| Bicarbonate | 0–250 ppm |
| pH | pH 5.0–10.5 |

The main table shows whether the current value is below, within, or above the
broad brewing reference band. Expanding a value row shows the full historical
chart, historical MWRA range, fixed chart scale, and a matching green swatch for
the chart's reference band. These bands are broad guidance ranges, not recipe
targets. Exact targets still depend on beer style, grist, sparge process, and
measured mash pH.

Each expanded chart can be switched between `3 months`, `6 months`, `Year to
date`, `1 year`, and `All time`. The rolling `3 months`, `6 months`, and `1
year` views reserve space for every month in the selected interval and leave
gaps where the local CSV has no value. `Year to date` and `All time` show only
months with available local data.

pH is already a logarithmic measurement of hydrogen ion activity. The pH chart
is therefore plotted evenly in pH units and labels pH values explicitly rather
than re-transforming them a second time.

## Optional recipe-software exports

The displayed water profile can be entered manually into any brewing water
calculator that accepts the listed ions and pH. For convenience, the app also
offers optional recipe exports:

- a Brewfather recipe JSON containing the selected month's water profile;
- a matching BeerXML recipe generated from the same sanitized temporary batch.

These are compatibility features, not the app's primary purpose. The app does
**not** connect to brewing-software APIs, modify external accounts, or create
reusable profiles in those services.

The Brewfather download is  a blank recipe export with dummy data, that can then
be altered by the author to the recipe they are planning to brew. The BeerXML follows
the same process, but based on the BeerXML 1.0 standards.

## Conversion rules

| Output | Calculation |
| --- | --- |
| Values reported in mg/L | `1 mg/L = 1 ppm` |
| Values reported in µg/L or ug/L | `value / 1000 = ppm` |
| Bicarbonate | `alkalinity as CaCO3 × 1.22` |
| pH | No conversion |

The default MWRA source column is:

```text
Wachusett System / Metro-Boston / Carroll Water TP Finished Water Tap / Treated
```

## Requirements

- Python 3.12 or newer
- Internet access on first run and whenever MWRA posts a newly linked report
- A modern web browser

No database, JavaScript build system, brewing-software account, credentials,
or API keys are required.

## Administrator configuration

Administrators can change two commonly updated behaviors without editing
Python or JavaScript. Edit [`app-config.toml`](app-config.toml) in the project
root—the same directory that contains `README.md` and `pyproject.toml`.

### How to update the configuration

1. Stop the running server with `Ctrl+C`.
2. Open `app-config.toml` in a plain-text editor.
3. Change only the value of `mwra_reports_page_url` or the entries inside
   `main_profile_fields`.
4. Preserve TOML syntax: URLs and field names need quotation marks, list items
   need commas, and square brackets must remain around the field list.
5. Save the file.
6. Start the server again:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Reload the web page and confirm the report list and main profile table look
   as expected.

On Windows PowerShell, the editing and restart process is the same after
activating the virtual environment:

```powershell
uvicorn app.main:app --reload
```

Configuration changes are loaded when the application starts. Restarting is
required even when Uvicorn was originally launched with `--reload`.

### Complete configuration example

```toml
mwra_reports_page_url = "https://www.mwra.com/your-water-system/drinking-water-quality/monthly-water-quality-test-results"

main_profile_fields = [
  "calcium",
  "magnesium",
  "sodium",
  "chloride",
  "sulfate",
  "bicarbonate",
  "ph",
]
```

### Changing the MWRA report-page URL

- `mwra_reports_page_url` is the MWRA page containing links to the monthly
  report PDFs—not the URL of an individual PDF.
- If MWRA moves its monthly-results page, replace the URL between the quotation
  marks and restart the application.
- Relative PDF links discovered on that page are resolved against this
  configured URL, and the footer’s MWRA source link is updated automatically.

Example:

```toml
mwra_reports_page_url = "https://www.example.org/new-monthly-report-page"
```

### Choosing the main water-profile fields

- `main_profile_fields` controls which values appear immediately in the main
  water-profile table and their order. All other extracted numeric values move
  into the expandable “Other metrics” rows at the bottom of that same table.
- Field keys are lowercase and use underscores instead of spaces.
- Reordering the keys reorders the main table. Removing a key moves that value
  into Other metrics; adding a supported key promotes it.
- Standard calculated field keys are `calcium`, `magnesium`, `sodium`,
  `chloride`, `sulfate`, `bicarbonate`, and `ph`.
- Additional MWRA fields can also be promoted. Common keys include
  `alkalinity`, `hardness`, `chlorine_total`, `fluoride`, `iron`, `manganese`,
  `potassium`, `silica`, `specific_conductance`, `total_dissolved_solids`, and
  `total_organic_carbon`.

For example, this configuration promotes alkalinity and hardness while moving
sodium and pH into the collapsible section:

```toml
main_profile_fields = [
  "calcium",
  "magnesium",
  "alkalinity",
  "hardness",
  "chloride",
  "sulfate",
  "bicarbonate",
]
```

An unknown field key is skipped because no matching measurement exists in the
report. A field may also be absent from a particular month if MWRA did not
publish that numeric measurement.

### Configuration errors

The app validates the configuration at startup and reports a clear error for
missing, malformed, empty, or duplicate settings. If the app will not start
after an edit:

- check that the URL and every field key still have matching quotation marks;
- check that list entries are separated by commas;
- remove duplicate field keys;
- ensure `main_profile_fields` contains at least one entry;
- compare the file with the
  [repository’s default configuration](app-config.toml).

The configuration is intentionally committed to Git so deployments have an
auditable default. Administrators making environment-specific changes should
review those edits before pulling or deploying future repository updates.

## Measurement guidance

Every value in both the main table and the collapsible measurements section
has a tooltip explaining what it measures and its general relevance to
brewing. These notes are static educational context; they do not assess
whether the selected month's value is high, low, safe, or appropriate for a
particular recipe.

The brewing guidance was synthesized primarily from Martin Brungard's
[Bru'n Water: Water Knowledge](https://www.brunwater.com/water-knowledge),
including its discussions of mash pH, alkalinity, hardness, major ions,
undesirable metals, nitrate, and chlorine removal. Always calculate treatment
for the actual recipe and verify source data against the MWRA PDF.

## Run on macOS or Linux

Clone the repository:

```bash
git clone https://github.com/vincemancuso/mwra-import.git
cd mwra-import
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the application:

```bash
python -m pip install -e .
```

Start the local server:

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

The first run may take longer than later page loads because the app builds its
local cache from the monthly reports currently linked on the MWRA page. After
that, it reads previously extracted raw values from `data/mwra-treated-water-values.csv`
and only downloads/parses newly discovered report months.

Stop the server with `Ctrl+C`. Leave the virtual environment with:

```bash
deactivate
```

## Run on Windows PowerShell

Clone the repository and enter it:

```powershell
git clone https://github.com/vincemancuso/mwra-import.git
cd mwra-import
```

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, allow it for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install and run the app:

```powershell
python -m pip install -e .
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

The first run may take longer than later page loads while the local CSV and PDF
cache are created.

## Development and tests

Install the development dependencies:

```bash
python -m pip install -e '.[dev]'
```

On Windows PowerShell, quote the same argument:

```powershell
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

The suite covers:

- report-link discovery and latest-month selection;
- CSV-backed raw-value caching;
- brewing-ready and raw CSV exports;
- independent unit conversion calculations;
- extraction from a synthetic MWRA-style fixture PDF;
- the HTML page and local API/PDF endpoints.

The fixture PDF can be regenerated with:

```bash
python tests/fixtures/generate_fixture.py
```

## Local API

The browser interface uses these local endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Render the web interface |
| `GET /api/reports` | List all linked reports and identify the latest one |
| `GET /api/history` | Return historical chart data for the configured main brewing values |
| `GET /api/exports/brewing-values.csv` | Download brewing-related values across all stored months in brewing-ready units |
| `GET /api/exports/raw-values.csv` | Download every stored MWRA measurement across all stored months in original units |
| `GET /api/reports/{year}/{month}` | Return one selected report profile |
| `GET /api/reports/{year}/{month}/pdf` | Stream one selected cached report PDF |
| `GET /api/reports/{year}/{month}/brewfather.json` | Download a Brewfather recipe containing the selected water profile |
| `GET /api/reports/{year}/{month}/beerxml.xml` | Download the same temporary recipe as BeerXML |
| `GET /api/latest` | Return report metadata, raw measurements, conversions, and display values |
| `GET /api/latest/pdf` | Stream the cached MWRA source PDF |

Interactive FastAPI documentation is available while the app is running:

- <http://127.0.0.1:8000/docs>
- <http://127.0.0.1:8000/redoc>

## Project structure

```text
app/
  config.py       Application paths and fixed internal constants
  conversions.py  Unit and bicarbonate calculations
  discovery.py    Latest-report link discovery
  main.py         FastAPI routes
  models.py       Pydantic response models
  parser.py       PDF table and text extraction
  report_store.py CSV-backed raw-value storage
  settings.py     Root TOML configuration loading and validation
  service.py      Discovery, cache refresh, and response workflow
  water_context.py Measurement display partitioning and tooltip guidance
app-config.toml    Administrator-editable source URL and main field list
static/            Plain CSS and JavaScript
templates/         Jinja2 HTML template
tests/             Unit, parser, discovery, and endpoint tests
data/reports/      Local PDF cache; downloaded PDFs are ignored by Git
data/mwra-treated-water-values.csv
                   Local raw-value CSV cache; ignored by Git
clear_local_data.py
                   Manual maintenance script to delete local cached data
refresh_local_data.py
                   Manual maintenance script to delete and rebuild local data
```

## How report caching works

On startup/page load, the app checks the configured MWRA monthly-results page
for linked report PDFs. It compares those report months with the local CSV at
`data/mwra-treated-water-values.csv`.

- If a month already exists in the CSV, the app uses those stored raw MWRA
  values and converts them into brewing units in memory.
- If MWRA has linked a month that is not in the CSV, the app downloads that PDF
  into `data/reports/`, extracts the treated-water measurements, and adds a new
  month column to the CSV.
- On a fresh clone, neither the CSV nor cached PDFs are included. The first run
  creates both from the public MWRA reports page.

The CSV format is intentionally simple and inspectable. It uses one row per
raw measurement and one column per report month:

```csv
key,parameter,unit,source_label,2026-04,2026-05
calcium,Calcium,UG/L,Metro-Boston treated/finished water,4370,4320
ph,pH,standard units,Metro-Boston treated/finished water,9.7,9.6
```

The values in this file remain in their original MWRA units. The conversion to
ppm, bicarbonate, and display fields happens inside the app so configuration
changes do not require editing cached values.

To force a full local rebuild manually, stop the app and delete
`data/mwra-treated-water-values.csv` plus any PDFs you want refreshed from
`data/reports/`. The next run will recreate the cache from MWRA.

`data/mwra-treated-water-values.csv` and downloaded PDFs are ignored by Git so
the repository stays lightweight and each installation maintains its own local
cache.

## Manual cache maintenance scripts

Two standalone Python scripts are available in the project root for local
maintenance. They are not web endpoints and are not called by the FastAPI app.

Both scripts print a warning before deleting anything. When possible, they also
check the current MWRA report page and list any CSV months that are present
locally but are no longer linked on the MWRA website. If you delete those
months, the values may not be recoverable from MWRA later.

To remove all local cached MWRA data:

```bash
python clear_local_data.py
```

This clear-only script uses only the Python standard library, so it can run
even before the app dependencies are installed.

To remove all local cached MWRA data and immediately rebuild it from the
currently linked MWRA reports:

```bash
python refresh_local_data.py
```

The refresh script needs the app dependencies because it downloads and parses
PDFs. If it cannot import them, it exits before deleting anything and tells you
to activate the virtual environment and run `python -m pip install -e .`.

Each script requires typing an exact confirmation phrase before it deletes the
CSV or cached PDFs.

## Known limitations

- PDF parsing depends on the structure and wording of MWRA reports. A future
  MWRA layout change may break extraction.
- The parser uses the rightmost treated/finished-water column as a fallback
  when it cannot identify the preferred column directly.
- There is no manual PDF upload fallback yet.
- The app always selects the newest **linked** monthly report. Unlinked future
  placeholders on the MWRA page are ignored.
- Values are snapshots from MWRA's monthly report and may not represent water
  at a particular home, date, or tap.
- The app is intended for local personal use, not unattended public hosting.
- Optional third-party export formats may evolve. Generated recipe files
  should be checked after import.

When required values cannot be extracted, the app returns a descriptive error
instead of silently inventing or substituting values.

## Public hosting security notes

The app is intentionally lightweight, but it now includes a few defensive
defaults for internet-facing deployments:

- browser security headers, including a same-origin content security policy;
- month/year route validation before selected-report lookup;
- same-origin filtering for report links discovered from the configured MWRA
  page;
- size limits for downloaded report pages and PDFs;
- CSV export escaping for spreadsheet-formula-looking text.

If you deploy this publicly, place it behind a normal reverse proxy or platform
edge that provides HTTPS, access logs, request-size limits, and any rate
limiting you want. Keep `app-config.toml` administrator-controlled; do not
expose a public UI for changing the MWRA source URL without adding stronger
allow-listing.

## Troubleshooting

### `python3` or `py` cannot find Python 3.12

Install a current Python release from <https://www.python.org/downloads/> and
recreate the virtual environment.

### The app cannot fetch MWRA

Confirm that the machine can reach `www.mwra.com`. Corporate proxies, DNS
filters, or a temporary MWRA outage can prevent discovery or download.

### Parsing suddenly fails

Open the source PDF from the interface and compare its mineral-analysis table
with previous reports. MWRA may have changed the document layout. Please open a
GitHub issue with the report month and public MWRA PDF URL; do not upload
private files or credentials.

### Port 8000 is already in use

Choose another port:

```bash
uvicorn app.main:app --reload --port 8001
```

Then open <http://127.0.0.1:8001>.

## Data and affiliation disclaimer

MWRA, Brewfather, and other third-party names are used only to identify the
public data source and compatible software or formats. This project is not
affiliated with, endorsed by, or maintained by the Massachusetts Water
Resources Authority, Brewfather, or any brewing-software vendor.

Always verify extracted values against the embedded original PDF before using
them. Brewing decisions remain the user's responsibility.
