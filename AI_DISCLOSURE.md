# AI / Vibecoding Disclosure

This repository is intentionally and explicitly disclosed as **vibecoded**.

The initial version was created through an AI-assisted development session with
OpenAI Codex. The repository owner supplied the product requirements, selected
the behavior and scope, reviewed the running application, and authorized its
publication. Codex generated and edited much of the Python, HTML, CSS,
JavaScript, tests, and documentation.

## What was verified

At the time of the initial publication:

- the automated test suite passed;
- report selection was tested independently using fixture HTML;
- conversion calculations were tested independently;
- PDF extraction was tested using a generated fixture PDF;
- the parser was run against a live MWRA monthly report;
- the local interface, clipboard action, details table, and embedded PDF were
  exercised in a browser.

## What this does not guarantee

AI-generated code can contain incorrect assumptions, brittle logic, security
issues, or subtle defects even when tests pass. In particular:

- this code has not received an independent professional security audit;
- the water-chemistry calculations have not been certified by MWRA,
  Brewfather, or a water-treatment professional;
- future changes to MWRA's website or PDF layout may break discovery or
  extraction;
- automated tests cover known behavior, not every possible report format or
  failure mode.

Users should inspect the source, review the raw MWRA values shown by the app,
and confirm the result against the original PDF.

## Contributions

Human-written and AI-assisted contributions are both welcome. Contributors
should disclose material AI assistance in their pull request when it generated
or substantially rewrote code, tests, or documentation. Regardless of how a
change was produced, it should be reviewed and tested before merging.
