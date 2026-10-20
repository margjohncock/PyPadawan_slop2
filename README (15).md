# PyPadawan

A local guide for researchers who know basic Python and want to understand an unfamiliar
Python research repository. Follow one example through seven questions: purpose, inputs,
where to read, processing, trying it, recognising success and understanding settings.

**No paid APIs, AI services or model downloads. Inspected projects are never imported,
installed or executed.** After installing PyPadawan, inspection works offline.

## Install and open

Use Python 3.11 or later for PyPadawan. Download and extract this source repository, then
open a terminal in the extracted folder containing `app.py` and `pyproject.toml`.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

The first command creates an isolated environment for PyPadawan. The second installs
PyPadawan's dependencies. The third opens its local interface; stop it with Ctrl+C.
Installation needs package access or a previously prepared offline wheel collection.
`requirements-tested.txt` records the direct runtime versions used for local verification;
it is not a full dependency lock. To use that set, add `-c requirements-tested.txt` to the
installation command.

The research project may need a different Python version and its own environment. Do not
install its scientific dependencies into PyPadawan's environment just to inspect it.

## Use the guide

1. Upload a ZIP, choose a small bundled teaching example, or select **Local folder** and
   enter the full path to a downloaded repository. ZIPs retain the original 200-entry /
   10 MB expanded limits; local folders support up to 2,000 files after exclusions.
2. Choose the relevant project folder and example. A matching reviewed walkthrough appears
   first. Otherwise general inspection offers documented commands and reading candidates.
3. Move through the seven questions. Expand **Show evidence** to see exact files, lines or
   notebook cells. Reviewed teaching explanations and source observations are labelled separately.
4. In the running section, check prerequisites, working folder and recipe status. Commands
   are displayed for you to review and run separately; PyPadawan never runs them.
5. Turn off **Use matching reviewed walkthroughs** to see general inspection alone. Refresh
   local-folder inspection after editing files. Download the structured JSON report if useful.

Original configuration guidance and the `.gitignore` generator remain below the guided page.
Downloaded reports contain source/documentation excerpts; review them before sharing.

## Reviewed research tasks

| Project | First task | Important boundary |
| --- | --- | --- |
| [Molyso](https://github.com/modsim/molyso) | Understand an existing results table and its notebook | Header-preview orientation works without Molyso; original notebook has legacy pandas calls requiring review |
| [Gretel](https://github.com/SamStudio8/gretel) | Follow prepared sequencing inputs through one genomic region | Alignment, sorting, indexing and variant preparation are prerequisites |
| [Ef](https://github.com/epicf/ef_python) | Follow configuration into simulation snapshots and plotting | Stale script references and differing SymPy constraints need attention |

Guides are tied to reviewed source fingerprints, allowing CRLF/LF differences. The reviewed
revisions appear in the interface and guide YAML. Changed source withholds the scientific
walkthrough; general findings remain available. Unknown Python repositories do not require
a guide to receive inspection results. Scientific explanations beyond the evidence need
documentation or a maintained walkthrough.

To preview each research guide offline, use **Local folder** with the absolute path to
`tests/fixtures/molyso`, `tests/fixtures/gretel` or `tests/fixtures/ef_python` in this source
distribution. These are incomplete source-only test snapshots, not runnable research projects.
Use full upstream copies and appropriate data when following research commands.

## What is supported?

- Python source, module/function documentation and straightforward literal argparse options.
- Markdown and reStructuredText documentation, legacy `setup.py`, requirements, environment
  YAML, `pyproject.toml`, console commands and conventional `src/` packages.
- Python notebook cells, saved text output, INI-style configuration and CSV/TSV header previews.
- Source relationships and common file, column, summary, plotting and output operations.
- Specific gaps and discrepancies, rather than invented scientific explanations.

TIFF, BAM, HDF5 and other binary contents are not inspected. Dynamic packaging, arbitrary
shell syntax, custom configuration languages and general scientific interpretation are not
supported. Saved outputs do not establish a successful fresh run. Dependency parsing does not
solve environments or prove current compatibility. Commands and scientific results have not
been independently run for these research walkthroughs. Human novice sessions are pending.

## Develop and verify

Install development dependencies using your environment's Python:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

Tests cover original features, archive validation, source-only research snapshots, evidence
locations, changed guide sources, malformed files, notebook magics, configuration and UI
navigation. Upstream snapshot code is excluded from test collection and linting; it remains
unaltered research material. Tests never install or run those projects.

See [architecture, dependencies and fixture provenance](docs/ARCHITECTURE.md)
and the [novice walkthrough protocol](docs/NOVICE_WALKTHROUGH.md).
