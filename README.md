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
- Extracts the `Carroll Water TP Fin. Water Tap (Treated)` values.
- Converts MWRA units into standard brewing-water values in ppm.
- Displays calcium, magnesium, sodium, chloride, sulfate, bicarbonate, and pH.
- Expands to show the other numeric Carroll finished-water measurements found
  in the same MWRA report.
- Copies a ready-to-paste text profile to the clipboard.
- Compares each main profile value with the previous linked report using
  up, down, or steady indicators with exact prior values on hover or focus.
- Shows the raw MWRA measurements and conversion formulas.
- Embeds the original cached PDF for easy verification.

## Optional recipe-software exports

The displayed water profile can be entered manually into any brewing water
calculator that accepts the listed ions and pH. For convenience, the app also
offers two optional recipe exports:

- a Brewfather recipe JSON containing the selected month's water profile;
- a matching BeerXML recipe generated from the same sanitized temporary batch.

These are compatibility features, not the app's primary purpose. The app does
**not** connect to the Brewfather API, modify a Brewfather account, or create
reusable profiles in Brewfather.

The Brewfather download is based on a blank recipe export supplied during
development. It names the recipe `Dummy MWRA <Month YYYY> Recipe`, leaves
`author` blank, leaves `tags` unset, and fills the recipe's source, mash,
sparge, and total water blocks with the selected MWRA profile.

The BeerXML download is generated from that same in-memory temporary recipe,
uses an empty `BREWER`, and includes a standard BeerXML `WATERS/WATER` block.
It follows the BeerXML 1.0 required recipe record sets and data types.

Both export buttons include an in-app explanation of the temporary-recipe
workaround and its limitations.

The interface uses an original hop-and-water emblem and a cranberry, cream,
and olive palette inspired by the Boston Wort Processors' public club banner.
It does not reproduce the club's official logo.

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
- Internet access when fetching a report for the first time
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

- `main_profile_fields` controls which values appear in the main water-profile
  table and their order. All other extracted numeric values move into the
  collapsible “Other treated-water measurements” section.
- Field keys are lowercase and use underscores instead of spaces.
- Reordering the keys reorders the main table. Removing a key moves that value
  into the collapsible section; adding a supported key promotes it.
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
- independent unit conversion calculations;
- extraction from a synthetic MWRA-style fixture PDF;
- the HTML page and local API/PDF endpoints.

The fixture PDF can be regenerated with:

```bash
python tests/fixtures/generate_fixture.py
```

## Local API

The browser interface uses two local endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Render the web interface |
| `GET /api/reports` | List all linked reports and identify the latest one |
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
  settings.py     Root TOML configuration loading and validation
  service.py      Download, cache, parse, and response workflow
  water_context.py Measurement display partitioning and tooltip guidance
app-config.toml    Administrator-editable source URL and main field list
static/            Plain CSS and JavaScript
templates/         Jinja2 HTML template
tests/             Unit, parser, discovery, and endpoint tests
data/reports/      Local PDF cache; downloaded PDFs are ignored by Git
```

## How report caching works

On the first request for a month, the app downloads that linked MWRA report
into `data/reports/`. Later requests in the same running process reuse the
parsed profile, and later app starts reuse a valid cached PDF with the same
report month.

To force a fresh download manually, stop the app and delete the relevant PDF
from `data/reports/`. The next request will download it again.

## Known limitations

- PDF parsing depends on the structure and wording of MWRA reports. A future
  MWRA layout change may break extraction.
- The parser uses the rightmost treated/finished-water column as a fallback
  when it cannot identify the preferred column directly.
- There is no manual PDF upload fallback in this MVP.
- The app always selects the newest **linked** monthly report. Unlinked future
  placeholders on the MWRA page are ignored.
- Values are snapshots from MWRA's monthly report and may not represent water
  at a particular home, date, or tap.
- The app is intended for local personal use, not unattended public hosting.
- Optional third-party export formats may evolve. Generated recipe files
  should be checked after import.

When required values cannot be extracted, the app returns a descriptive error
instead of silently inventing or substituting values.

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
