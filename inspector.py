"""Inspect Python projects without executing their code."""
import ast
import os
from pathlib import Path

from source_reader import read_text
from understanding import build_understanding

SKIP_DIRS = {'.git', '.venv', 'venv', 'env', 'node_modules', '__pycache__', '.tox', '.nox', 'site-packages', 'dist', 'build', '__MACOSX', '.ipynb_checkpoints', '.pytest_cache', '.ruff_cache', '.mypy_cache'}


def find_project_root(extraction_root):
    """Unwrap a single enclosing directory (common in GitHub ZIP files)."""
    root = Path(extraction_root)
    children = [p for p in root.iterdir() if p.name not in {'__MACOSX', '.DS_Store'}]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return root


def inspect_project(project_dir, use_reviewed=True):
    root = Path(project_dir).resolve()
    if not root.is_dir():
        raise ValueError('Project directory does not exist')

    python_files, pyprojects, gitignores, test_dirs, ci_files = [], [], [], [], []
    imports, errors = set(), []
    all_files = []

    for directory, dirs, filenames in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(directory) / d).is_symlink())
        current = Path(directory)
        if current.name == 'tests':
            test_dirs.append(current)
        for filename in sorted(filenames):
            path = current / filename
            if path.is_symlink() or not path.is_file():
                continue
            all_files.append(path)
            if len(all_files) > 2000:
                raise ValueError('Project contains more than 2,000 inspectable files; choose a smaller folder')
            if filename.endswith('.py'):
                python_files.append(path)
            elif filename == 'pyproject.toml':
                pyprojects.append(path)
            elif filename == '.gitignore':
                gitignores.append(path)
            if filename.endswith(('.yml', '.yaml')) and current.name == 'workflows' and current.parent.name == '.github':
                ci_files.append(path)

    for path in python_files:
        try:
            tree = ast.parse(read_text(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imports.add(node.module.split('.')[0])
        except (SyntaxError, UnicodeError, OSError, ValueError, RecursionError) as error:
            errors.append(f'{path.relative_to(root)}: {error}')

    def paths(items):
        return sorted(p.relative_to(root).as_posix() for p in items)

    return {
        'understanding': build_understanding(root, all_files, use_reviewed=use_reviewed),
        'python_files': paths(python_files),
        'imports': sorted(imports),
        'has_pyproject': (root / 'pyproject.toml').is_file(),
        'has_gitignore': (root / '.gitignore').is_file(),
        'has_tests': (root / 'tests').is_dir(),
        'has_ci': any(p.parent == root / '.github' / 'workflows' for p in ci_files),
        'pyproject_files': paths(pyprojects),
        'gitignore_files': paths(gitignores),
        'test_directories': paths(test_dirs),
        'ci_files': paths(ci_files),
        'errors': errors,
    }
