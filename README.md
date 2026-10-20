# PyPadawan: understand and run a research project

A local Streamlit guide for researchers who know basic Python but are unfamiliar
with navigating a repository. Follow one example through seven questions, from
purpose and data requirements to analysis, running it and checking its result.

**No AI services, API credits or model downloads. Uploaded projects are never
imported, installed or executed.** Explanations come from the author's documentation
and a limited vocabulary of source-code patterns. Undocumented scientific methods
remain explicitly unknown.

## Install and open

Use Python **3.11 or newer**. Extract the source ZIP and open a terminal in the
folder containing `app.py`. Internet access is needed to install PyPadawan's
dependencies; inspection itself requires no external service.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m streamlit run app.py
```

These commands install **PyPadawan itself**, not any project you later upload.
The `[dev]` extra adds pytest and Ruff; omit it for normal use. Open the local
browser address printed by Streamlit (normally `http://localhost:8501`). Press
Ctrl+C in the terminal to stop the app. Full interpreter paths avoid a separate
virtual-environment activation step.

## Try the page

1. Select **csv_analysis** from “Or try a bundled teaching example”, or upload a
   project ZIP. An uploaded ZIP takes precedence over the bundled selection.
2. Confirm the project folder inside the ZIP. Single GitHub wrapper folders are
   recognised automatically; the folder selector supports archives with several projects.
3. Select an example to follow. Documented run paths are prioritised, followed by
   documented filenames, main guards and notebooks. A filename is a reading
   candidate, not proof of the intended launch command.
4. Move through the seven questions using the menu and Next/Back. The selected
   example stays the same. Use **Show evidence** to inspect source lines or cells.
5. In the run section, choose your terminal and a documented installation route.
   Multiple supported manifests require an explicit choice. Commands are displayed
   for review and execution in your own trusted local copy; the app never runs them.
6. The original configuration guidance and `.gitignore` generator remain below
   the guided page. The JSON download includes the structured report and excerpts.

## What the seven questions provide

| Question | Evidence and explanation |
| --- | --- |
| What does this project do? | README purpose, method and expected-results sections; package descriptions; module docstrings. Missing scientific context is identified. |
| Could I use my data? | Documented layout and units; observed input calls and possible column/key accesses; headers from referenced CSV/TSV samples. |
| Where should I start reading? | At most five connected files or notebook cells, local import relationships and directly matched calls, with up to twelve definitions to explore. |
| What happens to the data? | Reading, missing-value handling, grouping, numerical summaries, plotting and output calls; custom-function documentation and return expressions. This is not an execution trace. |
| How do I try one example? | Root manifest evidence, terminal-specific environment templates and a documented run command with explanations. Missing commands are not invented. |
| How will I know it worked? | Documented reference results and saved notebook text, separated from calls that merely attempt to write or display results. Tests are shown without claiming they pass. |
| What do settings mean? | Literal argparse options, defaults and help text; function defaults and referenced uppercase constants from the selected reading route. Dynamic declarations need review. |

Every content card is labelled **Documented by the author**, **Observed in source**
or **Not established**. Documentation can be incomplete or wrong. A static match
does not prove an object's runtime type or establish scientific validity.

## Maintained teaching projects

The `examples/` directory includes:

- `csv_analysis`: documented pandas analysis, sample CSV, input/output settings and reference means.
- `package_analysis`: a `src/` package and a starting script that imports its calculation.
- `notebook_analysis`: Python notebook cells and a saved text result.
- `undocumented_script`: exposes gaps instead of inventing a research purpose.
- `ambiguous_setup`: pip and Conda manifests with no author-selected route.

These files are fixtures for reading, tests and teaching. The app never executes
them. Running a fixture independently is a separate action by its maintainer/user.
See [the expected CSV experience](docs/EXAMPLE_WALKTHROUGH.md).

## Structured inspection interface

`inspect_project(path)` preserves the original fields (`python_files`, `imports`,
configuration presence flags, location lists and `errors`) and adds `understanding`:

```text
understanding
  schema_version: 1
  questions: seven question identifiers and titles
  examples: [{id, path, sections}]
  files: [{path, kind, status}]
  warnings: inspection limitations and file errors
  limitations: plain-language boundaries
```

Each section contains `id`, `title` and `cards`. Each card contains `text`,
`basis` (`documented`, `observed` or `unknown`) and `evidence`. References contain
`path`, `line_start`, `line_end`, `cell` and `excerpt`. Lines are 1-based within the
file, or within the specified notebook cell. Additional fields carry the reading
route, definitions, installation alternatives and documented commands as appropriate.

The JSON download includes source and documentation excerpts and saved notebook
text. Review it before sharing. No source is sent to an AI provider.

## Limits

- Existing archive limits: **200 entries and 10 MB uncompressed**. Extraction rejects
  traversal paths, symlinks, encrypted entries, non-portable Windows names and
  duplicate case-insensitive paths. The bundled server configuration limits uploads
  to 10 MB compressed too. These are small-project limits, not a public-hosting sandbox.
- Supported text is UTF-8, including BOM. Files over **1 MB** are listed but not
  read. CSV/TSV header inspection uses the first 64 KB and shows at most 50 fields.
  Excel, binary datasets, external downloads and linked files are not read.
- Python analysis uses the host Python parser: newer syntax may be unreadable on
  an older host. Function and import matching is syntactic; dynamic imports,
  rebinding, framework entrypoints and complex object relationships are unresolved.
  The guide is not a complete dependency graph or execution trace.
- Source limits are 60 definitions and 200 calls per file/cell, 20 example choices,
  five reading-route files/cells, and 100 inspected cells per notebook. Subset views
  are bounded too. A different folder or smaller project can expose additional code.
- Only format 4 notebooks are supported. Non-Python code, magics and shell cells
  are skipped with warnings. Saved text outputs are historical evidence; uploaded
  HTML, widgets and binary outputs are not executed or rendered.
- README Markdown headings provide section categorisation. Unrecognised headings
  and other text formats may remain uncategorised prose. This is not automatic
  interpretation of every sentence or an explanation of undocumented algorithms.
- Requirements includes/options and direct URLs require manual review. Supported
  root manifests are `requirements.txt`, `environment.yml`/`.yaml` and package
  `pyproject.toml` files with a build declaration. Tool-only TOML is not treated as
  an installable package. YAML uses the safe loader, rejecting aliases, nesting over
  50 levels and over 10,000 parser events. Dependencies are not installed or solved.
- Git metadata, common environments/caches and build directories are skipped.
  Inspection does not follow filesystem symlinks. Tests and CI are never run.

## Privacy and hosting

ZIPs are extracted to temporary folders on the machine hosting Streamlit, then
removed at the end of each page run. The current upload bytes and report may stay
in Streamlit session memory; changing the selected project replaces the report.
Stop the local app to end its sessions. Remove secrets and sensitive data before
uploading. Session reports are not written to a database. Uploaded content is
displayed as inert text/code, and remote links are not fetched by the inspector.

The supplied configuration disables Streamlit usage statistics. A public hosted
deployment needs separate access controls, resource isolation and a retention policy.

## Verify and contribute

With development dependencies installed, use the environment's Python:

```bash
python -m pytest
python -m ruff check .
```

CI installs the app and runs tests/lint on Windows and Ubuntu with Python 3.11
and 3.14. Tests cover the original controls, every maintained example, exact
evidence references, navigation, terminal variants, parser failures, unsafe ZIPs,
network non-use and non-execution. AppTest exercises real analysis and rendering;
its upload test injects bytes at the Streamlit uploader boundary.

Human evaluation is a separate outstanding check. Use the
[novice walkthrough protocol](docs/NOVICE_WALKTHROUGH.md) with two or three real
researchers before treating the teaching experience as validated. No human results
are claimed by the automated tests.

This implementation starts at upstream commit `1359dbf`. It focuses on the one
Understand and run page. See [design reasoning](docs/DESIGN.md) and the release notes
for implementation choices, verification and limitations.
