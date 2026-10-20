"""Regression coverage for real legacy research source, never imported or run."""
import hashlib
import json
import shutil
import socket
import subprocess
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from document_reader import read_document
from inspector import inspect_project
from legacy_reader import read_configuration, setup_metadata
from project_readers import read_project_files
from walkthroughs import anchor_reference, load_guides

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'


def references(value):
    if isinstance(value, dict):
        if 'excerpt' in value and 'line_start' in value:
            yield value
        else:
            for child in value.values():
                yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


@pytest.mark.parametrize('name', ['molyso', 'gretel', 'ef_python'])
def test_real_sources_have_seven_consistent_sections_with_or_without_guide(name):
    root = FIXTURES / name
    for enabled in (False, True):
        report = inspect_project(root, use_reviewed=enabled)['understanding']
        assert report['examples']
        first = report['examples'][0]
        assert first.get('reviewed', False) == enabled
        assert len(first['sections']) == 7
        assert len(first['sections'][2]['route']) <= 5
        for section in first['sections']:
            assert section['cards']
            for card in section['cards']:
                assert card['evidence'] or card['basis'] == 'unknown'
        for ref in references(report):
            source = (root / ref['path']).read_text(encoding='utf-8')
            if ref['cell']:
                source = json.loads(source)['cells'][ref['cell'] - 1]['source']
                source = ''.join(source) if isinstance(source, list) else source
            lines = source.splitlines() or ['']
            assert 1 <= ref['line_start'] <= ref['line_end'] <= len(lines)
            assert ref['excerpt'] == '\n'.join(lines[ref['line_start'] - 1:min(ref['line_end'], ref['line_start'] + 19)])[:1800]
        json.dumps(report)


def test_all_guide_source_anchors_and_fingerprints_match():
    for guide in load_guides():
        root = FIXTURES / guide['id']
        for path, digest in guide['fingerprints'].items():
            assert hashlib.sha256((root / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest
        for section in guide['sections'].values():
            for card in section:
                assert card['anchors']
                for anchor in card['anchors']:
                    assert anchor_reference(root, anchor)['excerpt']


def test_changed_snapshot_withholds_the_walkthrough(tmp_path):
    shutil.copytree(FIXTURES / 'gretel', tmp_path, dirs_exist_ok=True)
    with (tmp_path / 'gretel/cmd.py').open('a', encoding='utf-8') as stream:
        stream.write('\n# edited locally\n')
    report = inspect_project(tmp_path)['understanding']
    assert report['walkthroughs'][0]['status'] == 'needs_review'
    assert not any(example.get('reviewed') for example in report['examples'])
    assert report['examples']


def test_general_inspection_discovers_legacy_entry_points_and_conflicts():
    ef = inspect_project(FIXTURES / 'ef_python', use_reviewed=False)['understanding']
    assert ef['entry_points'][0]['name'] == 'ef'
    assert ef['entry_points'][0]['path'] == 'src/ef/main.py'
    assert ef['examples'][0]['path'] == 'src/ef/main.py'
    discrepancies = ' '.join(item['text'] for item in ef['discrepancies'])
    assert 'sympy' in discrepancies and '<1.3' in discrepancies
    assert '../../main.py' in discrepancies
    values = [v for conf in ef['configurations'] for v in conf['values']]
    assert any(v['name'] == 'time_step_size' and v['value'] == '6.0e-12' for v in values)
    gretel = inspect_project(FIXTURES / 'gretel', use_reviewed=False)['understanding']
    assert gretel['examples'][0]['path'] == 'gretel/cmd.py'
    settings = ' '.join(c['text'] for c in gretel['examples'][0]['sections'][6]['cards'])
    assert '--paths' in settings and '100' in settings
    assert any('hanselx==0.0.92' in m['details'].get('dependencies', []) for m in gretel['manifests'])


def test_setup_reader_does_not_evaluate_imports_or_calls(tmp_path):
    marker = tmp_path / 'executed'
    text = f'''from setuptools import setup as configure
from pathlib import Path
Path({str(marker)!r}).write_text('bad')
requirements = ['numpy>=1.20']
configure(name='study', install_requires=requirements,
          version=get_version(), entry_points={{'console_scripts':['study=study.cli:main']}})
'''
    metadata = setup_metadata('setup.py', text)
    assert metadata['details']['dependencies'] == ['numpy>=1.20']
    assert metadata['details']['scripts'] == {'study': 'study.cli:main'}
    assert not marker.exists()
    assert not metadata['usable']


def test_configuration_preserves_raw_percent_and_supplied_values():
    values = read_configuration('example.conf', '[Output]\npattern = result_%07d.h5\nStep = 1e-9\n')
    assert [v['value'] for v in values] == ['result_%07d.h5', '1e-9']
    assert values[1]['name'] == 'Step'


def test_rst_is_structured_without_external_includes_or_raw_content(tmp_path):
    secret = tmp_path / 'private.txt'
    secret.write_text('PRIVATE_SENTINEL', encoding='utf-8')
    document = f'''Purpose
=======
Analyse a small example.

Inputs
------
Prepared observations.

.. include:: {secret}

.. raw:: html

   <script>PRIVATE_SCRIPT</script>

Usage
-----

::

   study data.conf
'''
    sections, commands = read_document('README.rst', document)
    assert any('inputs' in section['topics'] for section in sections)
    assert any(command['command'] == 'study data.conf' for command in commands)
    assert not any('PRIVATE_SENTINEL' in section['text'] for section in sections)
    # Raw source may be quoted as text; it is never rendered as HTML.


def test_large_notebook_magics_and_table_headers_remain_inspectable(tmp_path):
    notebook = {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {}, 'cells': [{
        'cell_type': 'code', 'metadata': {}, 'execution_count': None,
        'source': '%matplotlib inline\nimport pandas\ndata = pandas.read_table("data.tsv")',
        'outputs': [{'output_type': 'display_data', 'data': {'image/png': 'a' * 1_200_000}, 'metadata': {}}]}]}
    (tmp_path / 'analysis.ipynb').write_text(json.dumps(notebook), encoding='utf-8')
    (tmp_path / 'data.tsv').write_text('time\tlength\n' + '1\t2\n' * 300000, encoding='utf-8')
    report = read_project_files(tmp_path, list(tmp_path.iterdir()))
    assert report['tables'][0]['headers'] == ['time', 'length']
    assert report['sources'][0]['imports'][0]['module'] == 'pandas'
    assert any('Reads a delimited' in o['text'] for o in report['sources'][0]['operations'])
    assert report['sources'][0]['evidence']['excerpt'].startswith('%matplotlib')
    assert not report['saved_outputs']


def test_malformed_configuration_and_notebook_do_not_hide_other_sources(tmp_path):
    (tmp_path / 'bad.conf').write_text('[broken', encoding='utf-8')
    (tmp_path / 'bad.ipynb').write_text('{bad', encoding='utf-8')
    (tmp_path / 'good.py').write_text('print(1)', encoding='utf-8')
    report = inspect_project(tmp_path)['understanding']
    assert len(report['warnings']) == 2
    assert report['examples'][0]['path'] == 'good.py'


def test_inspection_never_imports_sphinx_or_runs_commands(tmp_path, monkeypatch):
    marker = tmp_path / 'executed'
    payload = f'from pathlib import Path\nPath({str(marker)!r}).write_text("bad")\n'
    (tmp_path / 'conf.py').write_text(payload, encoding='utf-8')
    (tmp_path / 'setup.py').write_text(payload, encoding='utf-8')
    (tmp_path / 'README.rst').write_text('.. automodule:: conf\n\n.. include:: https://example.invalid/file', encoding='utf-8')

    def forbidden(*args, **kwargs):
        pytest.fail('Inspection attempted a command or connection')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    inspect_project(tmp_path)
    assert not marker.exists()


@pytest.mark.parametrize('name', ['molyso', 'gretel', 'ef_python'])
def test_local_folder_walkthrough_renders_all_questions(name):
    app = AppTest.from_file(ROOT / 'app.py', default_timeout=30).run()
    app.radio[0].set_value('Local folder').run()
    app.text_input[0].set_value(str(FIXTURES / name))
    next(button for button in app.button if button.label == 'Inspect folder').click().run()
    assert not app.exception
    example = next(box for box in app.selectbox if box.label == 'Example to follow')
    assert example.value == 'guide:' + name
    for index in range(7):
        next(box for box in app.selectbox if box.label == 'Your questions').set_value(index).run()
        assert not app.exception
        assert next(box for box in app.selectbox if box.label == 'Example to follow').value == 'guide:' + name
    next(box for box in app.selectbox if box.label == 'Your questions').set_value(4).run()
    next(box for box in app.selectbox if box.label == 'Your terminal').set_value('macOS / Linux').run()
    assert not app.exception
    app.checkbox[0].set_value(False).run()
    assert not app.exception
    assert not next(box for box in app.selectbox if box.label == 'Example to follow').value.startswith('guide:')
