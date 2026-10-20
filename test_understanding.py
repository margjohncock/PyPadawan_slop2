import json
from pathlib import Path

import pytest

from inspector import inspect_project
from understanding import QUESTIONS, command_mentions

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


def example_report(name):
    return inspect_project(EXAMPLES / name)['understanding']


def text_in(section):
    return '\n'.join(card['text'] for card in section['cards'])


@pytest.mark.parametrize('name', ['csv_analysis', 'package_analysis', 'notebook_analysis',
                                  'undocumented_script', 'ambiguous_setup'])
def test_every_example_has_seven_supported_or_unknown_sections(name):
    report = example_report(name)
    assert report['examples']
    assert not report['warnings']
    assert len(report['examples'][0]['sections']) == 7
    for example in report['examples']:
        assert [s['id'] for s in example['sections']] == [key for key, _ in QUESTIONS]
        for section in example['sections']:
            assert section['cards']
            for card in section['cards']:
                assert card['basis'] in {'documented', 'observed', 'unknown'}
                if card['basis'] != 'unknown':
                    assert card['evidence']
    json.dumps(report)


def collect_references(value):
    if isinstance(value, dict):
        if {'path', 'line_start', 'line_end', 'excerpt', 'cell'} <= value.keys():
            yield value
        else:
            for child in value.values():
                yield from collect_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from collect_references(child)


@pytest.mark.parametrize('name', ['csv_analysis', 'package_analysis', 'notebook_analysis',
                                  'undocumented_script', 'ambiguous_setup'])
def test_all_evidence_points_to_real_exact_source(name):
    for ref in collect_references(example_report(name)):
        path = EXAMPLES / name / ref['path']
        assert path.is_file()
        source = path.read_text(encoding='utf-8')
        if ref['cell'] is not None:
            cell = json.loads(source)['cells'][ref['cell'] - 1]
            source = cell['source']
            source = ''.join(source) if isinstance(source, list) else source
        lines = source.splitlines() or ['']
        assert 1 <= ref['line_start'] <= ref['line_end'] <= len(lines)
        expected = '\n'.join(lines[ref['line_start'] - 1:min(ref['line_end'], ref['line_start'] + 19)])[:1800]
        assert expected == ref['excerpt']


def test_csv_walkthrough_answers_the_seven_questions():
    sections = example_report('csv_analysis')['examples'][0]['sections']
    assert 'compare average values' in text_in(sections[0])
    assert 'millimetres' in text_in(sections[1])
    assert 'header fields: group, value' in text_in(sections[1])
    assert "accesses 'group'" in text_in(sections[1])
    assert "accesses 'value'" in text_in(sections[1])
    assert len(sections[2]['route']) <= 5
    assert 'main calls summarise' in text_in(sections[2])
    processing = text_in(sections[3])
    for description in ('Reads a CSV', 'Removes missing', 'Groups rows', 'Calculates an average', 'Writes a table'):
        assert description in processing
    assert processing.index('Groups rows') < processing.index('Calculates an average')
    assert 'not an execution trace' in sections[3]['notice']
    running = sections[4]
    assert [r['path'] for r in running['installation_routes']] == ['requirements.txt']
    assert running['documented_commands'][0]['command'] == 'python analysis.py --input data/measurements.csv --output summary.csv'
    assert '.\\.venv\\Scripts\\python.exe' in running['installation_routes'][0]['commands']['windows'][1]['command']
    assert '.venv/bin/python' in running['installation_routes'][0]['commands']['posix'][1]['command']
    assert 'mean 3.0' in text_in(sections[5])
    assert 'not a reference result' in text_in(sections[5])
    assert '--input' in text_in(sections[6]) and "'data/measurements.csv'" in text_in(sections[6])


def test_src_package_links_to_the_actual_definition():
    first = example_report('package_analysis')['examples'][0]
    assert first['path'] == 'example.py'
    reading = first['sections'][2]
    assert any(step['path'] == 'src/measurement/core.py' for step in reading['route'])
    assert any(card.get('definition') == 'scale' and card.get('target') == 'src/measurement/core.py' for card in reading['cards'])
    assert 'DEFAULT_FACTOR' in text_in(first['sections'][6])


def test_notebook_sources_and_saved_text_have_provenance():
    example = example_report('notebook_analysis')['examples'][0]
    assert example['path'] == 'analysis.ipynb'
    assert example['sections'][2]['route'] == [{'path': 'analysis.ipynb', 'cell': 2}]
    assert 'Saved notebook text output (not freshly executed):\n3.0' in text_in(example['sections'][5])
    assert all(ref['cell'] is not None for ref in collect_references(example) if ref['path'].endswith('.ipynb'))


def test_undocumented_does_not_invent_research_purpose_or_command():
    sections = example_report('undocumented_script')['examples'][0]['sections']
    assert all(c['basis'] == 'unknown' for c in sections[0]['cards'])
    assert 'Scientific purpose cannot be established' in text_in(sections[0])
    assert not sections[4]['documented_commands']
    assert not sections[4]['installation_routes']
    assert 'No documented reference result' in text_in(sections[5])
    assert 'f.a (function default); default: 2' in text_in(sections[6])


def test_two_manifests_are_alternatives():
    running = example_report('ambiguous_setup')['examples'][0]['sections'][4]
    assert len(running['installation_routes']) == 2
    assert 'no route is selected automatically' in text_in(running)


def test_run_command_matching_does_not_confuse_shared_filenames():
    assert command_mentions('python "examples/a/run.py" --input x.csv', 'examples/a/run.py')
    assert not command_mentions('python examples/a/run.py', 'examples/b/run.py')
    assert not command_mentions('python myrun.py', 'run.py')
    assert command_mentions('python -m measurement', 'src/measurement/__main__.py')
