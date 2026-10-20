import io
import zipfile

import pytest

from archive_handler import extract_project_zip
from gitignore_generator import generate_gitignore
from inspector import find_project_root, inspect_project


def test_github_zip_project_root(tmp_path):
    folder = tmp_path / 'project-main'
    folder.mkdir()
    (folder / '.gitignore').write_text('*.pyc\n')
    (folder / 'pyproject.toml').write_text('[project]\nname="demo"\n')
    assert find_project_root(tmp_path) == folder
    result = inspect_project(folder)
    assert result['has_gitignore'] and result['has_pyproject']


def test_nested_config(tmp_path):
    nested = tmp_path / 'pkg'
    nested.mkdir()
    (nested / '.gitignore').write_text('*.tmp\n')
    (nested / 'pyproject.toml').write_text('')
    (nested / 'tests').mkdir()
    ci = nested / '.github' / 'workflows'
    ci.mkdir(parents=True)
    (ci / 'check.yaml').write_text('name: check\n')
    result = inspect_project(tmp_path)
    assert not result['has_gitignore']
    assert result['gitignore_files'] == ['pkg/.gitignore']
    assert result['pyproject_files'] == ['pkg/pyproject.toml']
    assert result['test_directories'] == ['pkg/tests']
    assert result['ci_files'] == ['pkg/.github/workflows/check.yaml']


def test_skip_venv(tmp_path):
    venv = tmp_path / '.venv'
    venv.mkdir()
    (venv / '.gitignore').write_text('')
    (venv / 'external.py').write_text('import hidden\n')
    assert inspect_project(tmp_path)['gitignore_files'] == []
    assert inspect_project(tmp_path)['imports'] == []


def test_deduplicate_templates():
    assert generate_gitignore(['Python', 'Python']).count('# Python cache files') == 1


def test_reject_zip_traversal(tmp_path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('../outside.txt', 'bad')
    stream.seek(0)
    with pytest.raises(ValueError):
        extract_project_zip(stream, tmp_path)


def test_extract_github_zip(tmp_path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('project-main/.gitignore', '*.pyc\n')
    stream.seek(0)
    extract_project_zip(stream, tmp_path)
    root = find_project_root(tmp_path)
    assert inspect_project(root)['has_gitignore']
