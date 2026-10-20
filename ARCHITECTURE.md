# Inspection and walkthrough design

PyPadawan 0.3 starts from original commit `1359dbf14f29f01bae33b84dffb690b7778226c3`.
The upload, setup guidance and gitignore generator remain available. Selected bounded
readers and regression tests from the intermediate offline implementation were reused
and extended; the earlier generated application is not the repository baseline.

## Data flow

1. A validated ZIP is extracted into a temporary directory, or the user selects a local folder.
2. The inspector skips symlinks, environments, caches and build directories. It lists original
   inspection fields and gathers documentation, manifests, code, notebook cells and configurations.
3. Readers create JSON-compatible evidence with project-relative paths, one-based source lines,
   and one-based notebook cell numbers. Parsing failure in one file does not hide other findings.
4. Local imports and unambiguous calls provide a bounded reading route. These relationships
   are observations, not an execution trace or a scientific explanation.
5. A matching bundled walkthrough can replace the main presentation with a short scientific
   learning task. Additional generic findings remain available in an expander.
6. Streamlit displays text and code excerpts. No uploaded HTML, commands, Python or notebooks run.

`inspect_project(path, use_reviewed=True)` retains the original report fields and adds
`understanding`. Its schema version is 2. That object contains seven-section `examples`,
`entry_points`, `configurations`, `manifests`, `discrepancies`, `walkthroughs`, file statuses,
warnings and limitations. A card's basis is `documented`, `observed`, `reviewed` or `unknown`.
Scientific facts are never generated from filenames or variable names.

## Why these dependencies?

| Dependency | Responsibility |
| --- | --- |
| Streamlit | Existing local interface and widget-state testing |
| packaging | Requirement syntax, versions, extras and markers; no dependency solving |
| PyYAML | Restricted environment files and application-owned teaching data |
| markdown-it-py | Structured Markdown headings and code blocks |
| Docutils | Restricted reStructuredText structure, without building Sphinx |
| nbformat | Notebook representation, without a kernel or execution client |

Python's `ast` reads definitions, signatures, calls, docstrings and supported packaging literals.
`configparser` reads INI-style configuration with interpolation disabled. `csv`, `tomllib` and
`json` supply text-format readers. There is no reason to install a second parser for these.

CodeTour, Pyan, Griffe and explainshell informed interaction and analysis choices. They are
not dependencies. PyPadawan does not need the research projects' NumPy, HDF5, microscopy or
bioinformatics stacks to inspect their source. Binary format inspection is deferred.

## Adding a walkthrough

Add an application-owned YAML file to `pypadawan_guides`, not to the uploaded repository.
There is no uploaded-plugin discovery or dynamic handler loading. The YAML schema is version 1:

- `id`, `title`, source `url` and reviewed `revision` identify the teaching snapshot.
- `example` is a readable Python file or notebook within that project.
- `fingerprints` maps every reviewed input file to SHA-256 of bytes with CRLF normalised to LF.
  All other source changes invalidate a match. No scientific walkthrough is applied on a partial match.
- `sections` supplies all seven question IDs. Each card has `text` and nonempty `anchors`.
- Each anchor has `path`, exact `contains` text and optional `cell`. The loader locates its real lines.
- `route` contains at most five anchors plus their teaching `role`.
- `recipe` contains its verification `status`, `prerequisites`, separate `windows` and `posix`
  steps (`command`, `cwd`, `explanation`) and `checkpoints`.

Check anchors and fingerprints against a source-only regression fixture and test a changed-source
case before shipping. The loader withholds stale or unresolved guides. Match status means source
matching, never that commands were run or that the science was independently validated.

## Limits

- Existing ZIP limits: 200 entries, 10 MB expanded; encrypted, symlink, traversal, duplicate and
  nonportable paths are rejected. Local folders are limited to 2,000 files after exclusions.
- Python/docs/configuration files: 1 MB each. Notebooks: 20 MB, first 100 cells. Notebook images
  are not rendered; saved text excerpts are bounded. CSV/TSV readers inspect a 64 KB prefix.
- Whole-cell magics and non-Python cells are skipped. Line magics are omitted with original
  line numbers preserved; the surrounding Python is inspected. Saved cell order is not execution order.
- Only literal, straightforward setup metadata and argparse declarations are understood.
  Dynamic setup expressions, arbitrary shell syntax, custom configuration languages and Jinja
  Conda recipes are not evaluated. Unsupported legacy Python syntax remains an explicit gap.
- Docutils raw content, automatic includes and configuration loading are disabled. Files under
  the selected root are read individually; Sphinx extensions and `conf.py` are never loaded.
- No network retrieval, dependency installation, tests, kernels or uploaded subprocesses are launched.
  Installation templates remain unverified; an old Python declaration is not current compatibility evidence.
- Binary TIFF/BAM/HDF5 contents, scientific units absent from documentation, performance and
  numerical correctness are not established by source inspection.

## Regression snapshot provenance

The folders under `tests/fixtures` contain selected unmodified source files, documentation
and one saved notebook from the following upstream revisions. Their licence notices are
retained in each folder.

| Folder | Upstream project | Revision |
| --- | --- | --- |
| molyso | https://github.com/modsim/molyso | 9ee9eaef5751e6e53c2673b62c94c8ddf5df692e |
| gretel | https://github.com/SamStudio8/gretel | eb1041aad4756ef61aa2442f9af13ee4c2f5372d |
| ef_python | https://github.com/epicf/ef_python | 47b751bcada2af7fc50cef587a48b1a3c12bcbba |

These are intentionally incomplete test inputs: large experimental data, sequencing files,
simulation outputs and unrelated modules are omitted. They must never be installed,
imported, executed or collected as tests. Their README files are original research-project
documentation that the inspection tests read, not additional PyPadawan user guides.

The small projects under `examples` likewise have their own README files as teaching inputs.
They demonstrate how PyPadawan handles documented purpose, usage and missing information.
PyPadawan itself has one user-facing README at the repository root.
