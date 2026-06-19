<p align="center">
  <img src="static/wort-water-mark.png" alt="Boston Wort Processors hop and water emblem" width="140">
</p>

<h1 align="center">MWRA Brewfather Water Profile</h1>

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
results for manual entry into Brewfather.

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
- Converts MWRA units into Brewfather-friendly values.
- Displays calcium, magnesium, sodium, chloride, sulfate, bicarbonate, and pH.
- Expands to show the other numeric Carroll finished-water measurements found
  in the same MWRA report.
- Copies a ready-to-paste text profile to the clipboard.
- Generates a Brewfather recipe JSON using the selected month's water profile.
- Generates a matching BeerXML recipe from the same sanitized temporary batch.
- Shows the raw MWRA measurements and conversion formulas.
- Embeds the original cached PDF for easy verification.

It does **not** connect to the Brewfather API, modify a Brewfather account, or
create reusable profiles in Brewfather.

The Brewfather download is based on a blank recipe export supplied during
development. It names the recipe `Dummy MWRA <Month YYYY> Recipe`, leaves
`author` blank, leaves `tags` unset, and fills the recipe's source, mash,
sparge, and total water blocks with the selected MWRA profile.

The BeerXML download is generated from that same in-memory temporary recipe,
uses an empty `BREWER`, and includes a standard BeerXML `WATERS/WATER` block.
It follows the BeerXML 1.0 required recipe record sets and data types.

Both export buttons include an in-app explanation of the temporary-recipe
workaround and why the formats cannot directly install a reusable Brewfather
water profile.

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

No database, JavaScript build system, Brewfather credentials, or API keys are
required.

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
  config.py       MWRA URLs, paths, and application settings
  conversions.py  Unit and bicarbonate calculations
  discovery.py    Latest-report link discovery
  main.py         FastAPI routes
  models.py       Pydantic response models
  parser.py       PDF table and text extraction
  service.py      Download, cache, parse, and response workflow
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
- Brewfather's recipe JSON format may evolve. The generated recipe is based on
  the supplied blank export schema and should be checked after import.

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

MWRA and Brewfather are third-party names used only to identify the public data
source and intended manual-entry destination. This project is not affiliated
with, endorsed by, or maintained by the Massachusetts Water Resources
Authority or Brewfather.

Always verify extracted values against the embedded original PDF before using
them. Brewing decisions remain the user's responsibility.
