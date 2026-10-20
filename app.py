"""Streamlit interface for PyPadawan."""
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from archive_handler import extract_project_zip
from gitignore_generator import GITIGNORE_TEMPLATES, generate_gitignore
from guidance import GUIDANCE, all_root_components_present
from inspector import find_project_root, inspect_project
from understanding_view import render_understanding


def show_guidance(key, found_at_root, locations):
    """Display an inspection status and an expandable explanation."""
    info = GUIDANCE[key]
    title = info['title']
    if found_at_root:
        st.success(f'{title}: Found at project root')
    elif locations:
        st.info(f'{title}: Found only in subdirectories')
    else:
        st.warning(f'{title}: Not found')

    with st.expander(f'Learn about {title} and what to do'):
        st.markdown('**What is it?**')
        st.write(info['what'])
        st.markdown('**Why might I need it?**')
        st.write(info['why'])
        st.markdown('**What should I do?**')
        st.write(info['how'])
        st.markdown('**Example**')
        st.code(info['example'], language=info['language'])
        if locations:
            st.markdown('**Locations found in this upload**')
            for location in locations:
                st.code(location, language=None)
        if key == 'gitignore':
            st.caption('Use the .gitignore generator further down this page to create suggested patterns.')


st.set_page_config(page_title='PyPadawan — Understand and run', page_icon='🐍')
st.title('PyPadawan')
st.write('Understand a Python research project, one example at a time.')
st.caption('Local inspection only. Uploaded Python, notebooks, tests and installation commands are never executed. No paid APIs or model downloads.')

uploaded = st.file_uploader('Upload your Python project as a ZIP', type=['zip'])
bundled = Path(__file__).parent / 'examples'
available = sorted(p.name for p in bundled.iterdir() if p.is_dir()) if bundled.is_dir() else []
demo = st.selectbox('Or try a bundled teaching example', ['Upload your own ZIP'] + available,
                    help='These small maintained projects demonstrate both complete information and documentation gaps.')
uploaded_bytes = uploaded.getvalue() if uploaded is not None else None
if uploaded_bytes is None and demo in available:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((bundled / demo).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                archive.write(path, demo + '/' + path.relative_to(bundled / demo).as_posix())
    uploaded_bytes = buffer.getvalue()
if uploaded_bytes is not None:
    project_id = hashlib.sha256(uploaded_bytes).hexdigest()
    with tempfile.TemporaryDirectory() as temporary:
        extraction_root = Path(temporary)
        try:
            extract_project_zip(io.BytesIO(uploaded_bytes), extraction_root)
            detected = find_project_root(extraction_root)
            folders = {'.': extraction_root}
            folders.update({p.relative_to(extraction_root).as_posix(): p
                            for p in sorted(extraction_root.rglob('*')) if p.is_dir()})
            default = detected.relative_to(extraction_root).as_posix()
            selected_root = st.selectbox('Project folder inside ZIP', list(folders),
                                        index=list(folders).index(default), key='root_' + project_id)
            project_root = folders[selected_root]
            report_key = 'understand-v1:' + project_id + ':' + selected_root
            if st.session_state.get('inspection_key') != report_key:
                st.session_state['inspection_result'] = inspect_project(project_root)
                st.session_state['inspection_key'] = report_key
            result = st.session_state['inspection_result']
        except (ValueError, zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError) as error:
            st.error(f'Unable to inspect ZIP: {error}')
            st.stop()

        render_understanding(result['understanding'], hashlib.sha256(report_key.encode()).hexdigest(), selected_root)
        st.download_button('Download inspection JSON', json.dumps(result, indent=2),
                           file_name='pypadawan-inspection.json', mime='application/json')
        st.caption('The download contains source and documentation excerpts. Review them before sharing.')
        st.divider()
        st.subheader('Original inspection and setup guidance')
        st.caption(f'Project root: {project_root.relative_to(extraction_root).as_posix()}')
        st.write('Python files:', result['python_files'])
        st.write('Detected imports (not necessarily dependencies):', result['imports'])

        st.subheader('Project configuration')
        show_guidance('pyproject', result['has_pyproject'], result['pyproject_files'])
        show_guidance('gitignore', result['has_gitignore'], result['gitignore_files'])
        show_guidance('tests', result['has_tests'], result['test_directories'])
        show_guidance('ci', result['has_ci'], result['ci_files'])

        if all_root_components_present(result):
            st.success('🎉 All four configuration components were found at the project root! The Force is strong with this one.')
            project_id = hashlib.sha256(uploaded_bytes).hexdigest()
            if st.session_state.get('celebrated_project') != project_id:
                st.balloons()
                st.session_state['celebrated_project'] = project_id
            st.caption('Presence does not guarantee valid configuration, meaningful tests or passing CI.')

        if result['errors']:
            st.subheader('Inspection warnings')
            for error in result['errors']:
                st.warning(error)

st.divider()
st.header('Generate a .gitignore')
st.write('Select the tools used by your project, preview the patterns, then download the file.')
selected_options = st.multiselect(
    'Select tools and environments',
    options=list(GITIGNORE_TEMPLATES),
    default=['Python', 'Virtual environments', 'pytest'],
)
gitignore_content = generate_gitignore(selected_options)
st.subheader('Preview')
st.code(gitignore_content or '# No options selected', language='text')
st.download_button(
    'Download .gitignore', data=gitignore_content, file_name='.gitignore',
    mime='text/plain', disabled=not gitignore_content,
)
st.caption('Review existing .gitignore rules before replacing any file.')
