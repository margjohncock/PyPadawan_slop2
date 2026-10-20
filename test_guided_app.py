from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


def widget(app, label):
    return next(box for box in app.selectbox if box.label == label)


def test_original_controls_remain_available():
    app = AppTest.from_file(APP, default_timeout=20).run()
    assert not app.exception
    assert len(app.get('file_uploader')) == 1
    assert any(button.label == 'Download .gitignore' for button in app.get('download_button'))
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert app.get('download_button')[0].disabled


def test_seven_sections_share_the_same_selected_example():
    app = AppTest.from_file(APP, default_timeout=20).run()
    widget(app, 'Or try a bundled teaching example').set_value('csv_analysis').run()
    assert not app.exception
    assert widget(app, 'Example to follow').value == 'analysis.py'
    for index in range(7):
        widget(app, 'Your questions').set_value(index).run()
        assert not app.exception
        assert widget(app, 'Example to follow').value == 'analysis.py'
        assert any(label.value in {'Documented by the author', 'Observed in source', 'Not established'} for label in app.caption)
    app.button(key=next(b.key for b in app.button if b.label == 'Back')).click().run()
    assert widget(app, 'Your questions').value == 5
    next(b for b in app.button if b.label == 'Next').click().run()
    assert widget(app, 'Your questions').value == 6
    assert next(b for b in app.button if b.label == 'Next').disabled


def test_terminal_variants_and_source_evidence():
    app = AppTest.from_file(APP, default_timeout=20).run()
    widget(app, 'Or try a bundled teaching example').set_value('csv_analysis').run()
    widget(app, 'Your questions').set_value(4).run()
    assert not app.exception
    assert any('.\\.venv\\Scripts\\python.exe analysis.py' in code.value for code in app.code)
    widget(app, 'Your terminal').set_value('macOS / Linux').run()
    assert not app.exception
    assert any('.venv/bin/python analysis.py' in code.value for code in app.code)


@pytest.mark.parametrize('name', ['package_analysis', 'notebook_analysis', 'undocumented_script', 'ambiguous_setup'])
def test_other_bundled_projects_render(name):
    app = AppTest.from_file(APP, default_timeout=20).run()
    widget(app, 'Or try a bundled teaching example').set_value(name).run()
    assert not app.exception
    widget(app, 'Your questions').set_value(4).run()
    assert not app.exception
    assert any(button.label == 'Download inspection JSON' for button in app.get('download_button'))
    if name == 'ambiguous_setup':
        assert widget(app, 'Installation route').value == 'Follow the author’s instructions manually'
    if name == 'package_analysis':
        widget(app, 'Example to follow').set_value('src/measurement/core.py').run()
        widget(app, 'Your questions').set_value(2).run()
        assert widget(app, 'Example to follow').value == 'src/measurement/core.py'
