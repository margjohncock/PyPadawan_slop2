# Understand and run: implementation and verification

Implemented on 20 October 2026 from upstream commit
`1359dbf14f29f01bae33b84dffb690b7778226c3` (version 0.1.0), in a fresh local
checkout. Earlier generated implementation files are excluded. This source is
version **0.2.0** and focuses on the accepted seven-question page.

## Delivered

- Seven sections, shared example selection, Next/Back navigation and direct section selection.
- Documented, observed and not-established labels with source-file/cell evidence.
- Local readers for Python AST, README, manifests, notebook JSON and sample headers.
- Short reading routes, directly matched local definitions and supported operation explanations.
- Documented run commands, reviewed environment templates and terminal-specific explanations.
- Reference-output provenance, literal options, defaults and referenced constants.
- All five maintained teaching projects and a target walkthrough for the CSV example.
- Original ZIP upload, configuration guidance and `.gitignore` generator preserved.
- Duplicate template selections deduplicated to satisfy the repository's original regression test.
- Archive path checks strengthened for portable names and original ZIP filenames.
- Editable packaging metadata, CI dependency installation and a Windows/Linux Python matrix.
- Installation, scope, privacy, design reasoning and a human-evaluation protocol.

## Checks completed

- **70 tests passed**, including all 16 original tests. Coverage includes exact
  evidence references, all seven sections, example retention, navigation,
  terminal variants, unsupported inputs, local imports, ZIP handling and upload
  non-execution. A network-blocked inspection test verifies that the upload-to-guide
  pipeline does not connect to external services.
- Ruff lint: passed.
- Wheel build: passed.
- Editable installation into a separate virtual environment: passed, using
  preinstalled dependencies with network resolution disabled.
- Browser inspection of the CSV teaching example and expandable source evidence:
  passed. A preview image accompanies the source ZIP.
- Local platform: Windows, Python 3.14, Streamlit 1.66.0, pytest 9.1.1 and
  PyYAML 6.0.3. CI is configured for Python 3.11/3.14 on Windows/Ubuntu;
  those remote jobs have not been run here. macOS/Linux instructions have unit
  coverage but have not been executed on those operating systems.

## Outstanding before teaching usability is validated

The requested sessions with two or three novice researchers have **not** been
conducted; participants were not available in this workspace. Use
`docs/NOVICE_WALKTHROUGH.md` to recruit participants, record their answers and
revise recurring wording/navigation problems. Automated tests do not establish
that beginners understand the interface.

No paid API requests, model downloads, uploaded-code execution, GitHub push or PR
publication were performed. Undocumented scientific purpose and algorithms are
explicit gaps, rather than automatic claims. See README for technical limits.
