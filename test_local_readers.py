import json

import pytest

from inspector import inspect_project
from source_reader import MAX_SOURCE_BYTES, analyse_source


def test_dynamic_args_and_non_argparse_methods_need_review():
    text = ('import argparse\np = argparse.ArgumentParser()\n'
            'p.add_argument("--fixed", default=3, help="Number of repetitions")\n'
            'p.add_argument(*flags, default=compute())\n'
            'other.add_argument("--x", default=2)\n')
    settings = analyse_source('demo.py', text)['settings']
    assert settings[0]['supported']
    assert settings[0]['help'] == 'Number of repetitions'
    assert not settings[1]['supported']
    assert not settings[2]['supported']


@pytest.mark.parametrize(('filename', 'content'), [
    ('environment.yml', '!!python/object/apply:os.system ["forbidden"]'),
    ('environment.yml', 'dependencies: &recursive [*recursive]'),
    ('environment.yml', 'dependencies: ' + '[' * 51 + ']' * 51),
    ('environment.yml', 'dependencies: [22]'),
    ('environment.yml', 'channels: 4'),
    ('pyproject.toml', '[project'),
    ('pyproject.toml', '[project]\ndependencies="numpy"'),
    ('pyproject.toml', '[project]\ndescription=[]'),
    ('example.ipynb', '{"nbformat":4,"cells":[null]}'),
    ('example.ipynb', '{"nbformat":4,"cells":[],"metadata":[]}'),
    ('bad.py', 'def f('),
])
def test_bad_file_is_reported_without_hiding_good_evidence(tmp_path, filename, content):
    (tmp_path / filename).write_text(content, encoding='utf-8')
    (tmp_path / 'good.py').write_text('"""A documented example."""\nprint(2)', encoding='utf-8')
    report = inspect_project(tmp_path)['understanding']
    assert report['warnings']
    assert any(example['path'] == 'good.py' for example in report['examples'])


def test_requirement_includes_are_not_followed(tmp_path):
    (tmp_path / 'requirements.txt').write_text('numpy\n-r ../../private.txt\n--index-url https://example.invalid')
    (tmp_path / 'example.py').write_text('print(1)')
    running = inspect_project(tmp_path)['understanding']['examples'][0]['sections'][4]
    assert not running['installation_routes']


def test_large_and_non_utf8_files_are_bounded(tmp_path):
    (tmp_path / 'large.py').write_text('x' * (MAX_SOURCE_BYTES + 1))
    (tmp_path / 'bad.py').write_bytes(b'\xff\xfe')
    (tmp_path / 'good.py').write_text('print(1)')
    report = inspect_project(tmp_path)['understanding']
    assert len(report['warnings']) == 2
    assert [e['path'] for e in report['examples']] == ['good.py']


def test_magics_do_not_hide_other_notebook_cells(tmp_path):
    notebook = {'nbformat': 4, 'cells': [
        {'cell_type': 'code', 'source': '%%bash\necho no', 'outputs': []},
        {'cell_type': 'code', 'source': 'print(3)', 'outputs': []},
    ]}
    (tmp_path / 'example.ipynb').write_text(json.dumps(notebook))
    report = inspect_project(tmp_path)['understanding']
    assert 'magic' in report['warnings'][0]
    assert report['examples'][0]['sections'][2]['route'][0]['cell'] == 2


def test_relative_imports_and_cycles_have_a_bounded_route(tmp_path):
    package = tmp_path / 'pkg'
    package.mkdir()
    (package / '__init__.py').write_text('')
    (package / 'one.py').write_text('from .two import f\nif __name__ == "__main__":\n    f()')
    (package / 'two.py').write_text('from . import one\ndef f():\n    return 2')
    report = inspect_project(tmp_path)['understanding']
    route = report['examples'][0]['sections'][2]['route']
    assert 1 < len(route) <= 5
    assert len({(r['path'], r['cell']) for r in route}) == len(route)


def test_newer_syntax_error_does_not_stop_notebook(tmp_path):
    notebook = {'nbformat': 4, 'cells': [
        {'cell_type': 'code', 'source': 'def invalid(', 'outputs': []},
        {'cell_type': 'code', 'source': 'print(1)', 'outputs': []},
    ]}
    (tmp_path / 'analysis.ipynb').write_text(json.dumps(notebook))
    result = inspect_project(tmp_path)['understanding']
    assert result['warnings']
    assert result['examples']
