"""Plain-language guidance for PyPadawan inspection results."""

GUIDANCE = {
    'pyproject': {
        'title': 'pyproject.toml',
        'what': 'A TOML file describing your Python project and optionally configuring tools such as pytest and Ruff.',
        'why': 'It can make a project easier to install, share and maintain. Small standalone scripts do not always need one.',
        'how': 'Create pyproject.toml at your selected project root and add metadata appropriate to your project. A package may also need build configuration.',
        'example': '[project]\nname = "my-project"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n',
        'language': 'toml',
    },
    'gitignore': {
        'title': '.gitignore',
        'what': 'A file containing patterns for untracked files Git should ignore.',
        'why': 'It helps keep caches, virtual environments and local secrets out of new commits. Already-tracked files are not automatically removed.',
        'how': 'Create a .gitignore at the repository root or use the generator below. Review any existing rules before replacing the file.',
        'example': '__pycache__/\n*.py[cod]\n.venv/\n.env\n',
        'language': 'text',
    },
    'tests': {
        'title': 'Automated tests',
        'what': 'Code that checks whether your functions behave as expected.',
        'why': 'Tests can catch regressions as you change your code. A directory named tests does not guarantee working tests.',
        'how': 'Create a tests/ directory, add test_*.py files and install pytest. Replace the example with tests of your own functions.',
        'example': 'def add(a, b):\n    return a + b\n\ndef test_add():\n    assert add(2, 3) == 5\n',
        'language': 'python',
    },
    'ci': {
        'title': 'GitHub Actions',
        'what': 'Workflows that run jobs automatically in GitHub, for example when code is pushed.',
        'why': 'A workflow can run tests consistently on pull requests, but a workflow file existing does not mean its jobs pass.',
        'how': 'Add a YAML file inside .github/workflows/ at the repository root. Adapt installation and test commands to your project.',
        'example': 'name: Tests\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - run: python -m pip install pytest\n      - run: python -m pytest\n',
        'language': 'yaml',
    },
}


def all_root_components_present(result):
    """Check presence only, not whether configuration is valid or tests pass."""
    return all(result.get(key, False) for key in (
        'has_pyproject', 'has_gitignore', 'has_tests', 'has_ci'
    ))
