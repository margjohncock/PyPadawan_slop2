import io
import json
import socket
import stat
import zipfile
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from archive_handler import extract_project_zip
from inspector import find_project_root, inspect_project


def archive_bytes(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            entry = zipfile.ZipInfo()
            entry.filename = name
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, content)
    output.seek(0)
    return output


def test_upload_pipeline_never_executes_or_connects(tmp_path, monkeypatch):
    marker = tmp_path / 'executed.txt'
    code = f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\n'
    content = archive_bytes({
        'research-main/README.md': '# Project\nA documented example.\n## Usage\n```bash\npython run.py\n```',
        'research-main/run.py': code + 'if __name__ == "__main__":\n    print(3)\n',
        'research-main/setup.py': code,
        'research-main/test_run.py': code,
        'research-main/analysis.ipynb': json.dumps({'nbformat': 4, 'cells': [
            {'cell_type': 'code', 'source': code, 'outputs': []}]}),
        'research-main/requirements.txt': 'some-package @ https://example.invalid/package.whl',
    })
    def forbidden(*args, **kwargs):
        pytest.fail('Inspection attempted a network connection')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    destination = tmp_path / 'upload'
    destination.mkdir()
    extract_project_zip(content, destination)
    report = inspect_project(find_project_root(destination))
    assert report['understanding']['examples'][0]['path'] == 'run.py'
    assert not marker.exists()
    assert not report['understanding']['examples'][0]['sections'][4]['installation_routes']


@pytest.mark.parametrize('path', ['../escape', '/absolute', 'C:/drive', 'a\\b',
                                  'CON', 'NUL.txt', 'trailing.', 'bad\nname', 'x/../escape'])
def test_unsafe_archives_rejected_before_writing(tmp_path, path):
    with pytest.raises(ValueError):
        extract_project_zip(archive_bytes({'safe.txt': 'safe', path: 'unsafe'}), tmp_path)
    assert not (tmp_path / 'safe.txt').exists()


def test_links_and_case_collisions_rejected(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        entry = zipfile.ZipInfo('link')
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(entry, '../outside')
    buffer.seek(0)
    with pytest.raises(ValueError):
        extract_project_zip(buffer, tmp_path)
    with pytest.raises(ValueError):
        extract_project_zip(archive_bytes({'README.md': 'one', 'readme.md': 'two'}), tmp_path)


@pytest.mark.parametrize('files', [{f'{i}.txt': '' for i in range(201)}, {'large.txt': 'x' * 10_000_001}])
def test_resource_limits(tmp_path, files):
    with pytest.raises(ValueError):
        extract_project_zip(archive_bytes(files), tmp_path)


def test_actual_uploader_boundary_and_invalid_zip(monkeypatch):
    app_path = Path(__file__).resolve().parents[1] / 'app.py'
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **kw: archive_bytes({
        'demo-main/README.md': '# Demo\nAn uploaded example.',
        'demo-main/run.py': 'print(3)',
    }))
    app = AppTest.from_file(app_path, default_timeout=20).run()
    assert not app.exception
    assert next(b for b in app.selectbox if b.label == 'Example to follow').value == 'run.py'
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **kw: io.BytesIO(b'not a zip'))
    app.run()
    assert not app.exception
    assert any('Unable to inspect ZIP' in error.value for error in app.error)
