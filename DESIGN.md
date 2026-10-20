# Design decisions and reasoning

The accepted plan starts with upstream commit `1359dbf`; earlier generated code
is excluded. The page follows one researcher-selected example across seven sections.

1. **Purpose first.** Quote the author's description before asking the researcher
   to install anything. Scientific relevance cannot be determined by a file tree.
2. **Data before commands.** Show example headers, units and source accesses together,
   while distinguishing an observed key from a documented data requirement.
3. **A short reading route.** Follow a documented starting path and local connections;
   limit the route to five files/cells to avoid replacing confusion with a huge graph.
4. **Explain supported operations.** Tie a small vocabulary to source evidence. Custom
   algorithms use their own documentation and visible interfaces; static order is
   never presented as a runtime trace.
5. **One selected environment.** Offer explicit alternatives when manifests conflict.
   Explain commands and their working directory, and quote actual run instructions
   rather than guessing arguments from a filename.
6. **Separate attempted outputs from reference results.** File-writing calls alone
   cannot establish correctness. Preserve the provenance of saved notebook text.
7. **Keep settings relevant.** Show options, defaults and referenced constants from
   the selected reading route. Unsupported dynamic declarations remain review items.

## Repository references

- [CodeTour](https://github.com/microsoft/codetour): the model for a short guided
  route attached to specific files and source lines. Its tours are authored; this
  page constructs a limited route from local evidence and documentation.
- [Pyan](https://github.com/Technologicat/pyan): demonstrates static code relationships
  and their distinction from runtime call tracing. No Pyan or Graphviz dependency
  is introduced for the small first version.
- [Griffe](https://github.com/mkdocstrings/griffe): the reference for structured
  signatures, documentation and source locations. This extension builds on the
  repository's existing AST foundation; it does not import projects for inspection.
- [explainshell](https://github.com/idank/explainshell): the teaching model for
  explanations alongside command components. Only a small set of Python setup
  templates is authored here; a general shell interpreter is outside scope.

These are design references, not copied code or added services. Paid AI explanation,
chat, model downloads, automatic scientific interpretation and code execution are
outside this version. The absence of an explanation is made explicit rather than
filled by an unsupported guess.
