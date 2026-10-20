"""Streamlit views for the seven questions; all uploaded content is inert text."""
import hashlib
import re

import streamlit as st

BASIS = {'documented': 'Documented by the author', 'observed': 'Observed in source',
         'unknown': 'Not established', 'reviewed': 'Reviewed teaching explanation'}


def show_evidence(refs, label):
    with st.expander(label):
        for ref in refs:
            location = ref['path']
            if ref['cell'] is not None:
                location += f", cell {ref['cell']}"
            st.text(f"{location}, lines {ref['line_start']}–{ref['line_end']}")
            st.code(ref['excerpt'], language='python' if ref['path'].endswith(('.py', '.ipynb')) else None)
        st.caption('Excerpts are limited to 20 lines / 1,800 characters. Displayed line ranges refer to the original file or cell.')


def move_section(key, offset):
    st.session_state[key] = max(0, min(6, st.session_state.get(key, 0) + offset))


def render_run_recipe(current, identity, project_root):
    reviewed = current.get('reviewed_recipe')
    if reviewed:
        st.info(reviewed['status'])
        st.text(reviewed['prerequisites'])
        terminal = st.selectbox('Your terminal', ['Windows PowerShell', 'macOS / Linux'], key='terminal_' + identity)
        platform = 'windows' if terminal == 'Windows PowerShell' else 'posix'
        st.caption('Commands are displayed for you to review and run separately. PyPadawan does not run or install the research project.')
        for step in reviewed[platform]:
            st.text('Working folder: ' + step['cwd'])
            st.code(step['command'], language='powershell' if platform == 'windows' else 'bash')
            st.text(step['explanation'])
        for checkpoint in reviewed['checkpoints']:
            st.text('Check: ' + checkpoint)
        return
    st.write('Use your own extracted local copy. Every command below is display-only; review the repository before running it. Installation can execute dependency or build code.')
    st.text('Working folder: the selected project folder inside your local copy: ' + project_root)
    terminal = st.selectbox('Your terminal', ['Windows PowerShell', 'macOS / Linux'], key='terminal_' + identity)
    platform = 'windows' if terminal == 'Windows PowerShell' else 'posix'
    windows = platform == 'windows'
    navigate = ('cd "C:\\path\\to\\your-project"\nGet-Location\nGet-ChildItem' if windows else
                'cd "/path/to/your-project"\npwd\nls')
    st.code(navigate, language='powershell' if windows else 'bash')
    st.write('Replace the path with your selected local project folder. cd changes folder; the following commands show the current folder and its files. You should see the selected project’s manifest and example there.')
    routes = current['installation_routes']
    manual = 'Follow the author’s instructions manually'
    choice = st.selectbox('Installation route', [manual] + [r['path'] for r in routes],
                          index=1 if len(routes) == 1 and not current.get('requires_route_review') else 0, key='route_' + identity)
    selected = next((route for route in routes if route['path'] == choice), None)
    if selected:
        for step in selected['commands'][platform]:
            st.code(step['command'], language='powershell' if windows else 'bash')
            st.write(step['explanation'])
        show_evidence([selected['evidence']], 'Show evidence for the installation route')
        st.caption('Use the author’s Python version. These templates do not establish whether dependencies can be installed. For Conda, the activation command must be run in the same terminal.')
    if current['documented_commands']:
        st.markdown('**Documented commands for this example**')
        for number, command in enumerate(current['documented_commands'], 1):
            value = command['command']
            if selected and selected['kind'] != 'environment' and re.match(r'^python(?:3)?\s', value):
                executable = '.\\.venv\\Scripts\\python.exe' if windows else '.venv/bin/python'
                value = re.sub(r'^python(?:3)?', lambda match: executable, value, count=1)
                st.caption('Adapted to use the isolated environment’s Python. The original command is in the evidence.')
            st.code(value, language='powershell' if windows else 'bash')
            st.write(command['explanation'])
            show_evidence([command['evidence']], f'Show evidence for documented command {number}')
    else:
        st.info('A launch command has not been inferred from the filename. The missing instructions are listed above.')
    st.write('If a command fails, keep the full error message and check the current folder, Python version and required input files before changing the code. PyPadawan cannot diagnose a run it has not observed.')


def render_understanding(report, project_id, project_root):
    st.header('Understand and run the code')
    st.write('Follow one example from its purpose and input data to its analysis and expected result. '
             'This guide runs locally without AI services or API credits.')
    for status in report.get('walkthroughs', []):
        st.text(status['title'] + ': ' + status['status'].replace('_', ' '))
        st.caption(status.get('message', ''))
        if status.get('revision'):
            st.caption('Reviewed source revision: ' + status['revision'])
    if not report['examples']:
        st.info('No readable non-test Python example or supported Python notebook code cell was found. Check the file warnings below, or choose a different project folder.')
    else:
        by_id = {item['id']: item for item in report['examples']}
        example_id = st.selectbox('Example to follow', list(by_id),
                                 format_func=lambda key: by_id[key].get('title', key), key='example_' + project_id)
        example = by_id[example_id]
        identity = hashlib.sha256((project_id + example_id).encode()).hexdigest()
        st.caption('Documented filenames are prioritised, then main guards and notebooks. You can choose another reading candidate. This order does not establish the intended launch command.')
        menu_key = 'question_' + project_id
        index = st.selectbox('Your questions', list(range(7)),
                             format_func=lambda n: f"{n + 1}. {example['sections'][n]['title']}",
                             key=menu_key)
        current = example['sections'][index]
        st.subheader(f"{index + 1}. {current['title']}")
        for number, card in enumerate(current['cards'], 1):
            with st.container(border=True):
                st.caption(BASIS[card['basis']])
                if card.get('heading'):
                    st.text(card['heading'])
                st.text(card['text'])
                if card.get('description'):
                    st.text('Author’s description: ' + card['description'])
                if card.get('note'):
                    st.caption(card['note'])
                if card['evidence']:
                    show_evidence(card['evidence'], f'Show evidence — item {number}')
                for returned in card.get('returns', []):
                    st.text('Observed return expression: ' + returned['expression'])
                if card.get('definition'):
                    # The link opens the exact referenced definition within the page.
                    show_evidence(card['evidence'][-1:], f"Open related definition — {card['definition']} (item {number})")
        if current.get('notice'):
            st.info(current['notice'])
        if current.get('source_cards'):
            with st.expander('Additional source observations and documentation'):
                for card in current['source_cards']:
                    st.caption(BASIS[card['basis']])
                    st.text(card['text'])
                    for ref in card['evidence']:
                        st.text(f"{ref['path']} · line {ref['line_start']}" + (f" · cell {ref['cell']}" if ref['cell'] else ''))
                        st.code(ref['excerpt'], language=None)
        if index == 2 and current.get('definitions'):
            definitions = current['definitions']
            labels = [f"{d['evidence']['path']}:{d['evidence']['line_start']} — {d['name']}" for d in definitions]
            selected = st.selectbox('Explore a related function or class', labels, key='definition_' + identity)
            definition = definitions[labels.index(selected)]
            st.code(definition['signature'], language='python')
            st.text(definition['docstring'] or 'No purpose docstring was supplied.')
            st.text('Parameters: ' + (', '.join(p['name'] for p in definition['parameters']) or 'none declared'))
            for returned in definition['returns']:
                st.text('Returns: ' + returned['expression'])
            show_evidence([definition['evidence']], 'Show evidence for the selected definition')
        if index == 4:
            render_run_recipe(current, identity, project_root)
        previous, position, following = st.columns([1, 2, 1])
        previous.button('Back', on_click=move_section, args=(menu_key, -1), disabled=index == 0, key='back_' + project_id)
        position.caption(f'Section {index + 1} of 7 · following {example_id}')
        following.button('Next', on_click=move_section, args=(menu_key, 1), disabled=index == 6, key='next_' + project_id)
    st.caption(report['limitations'])
    if report['warnings']:
        with st.expander('Files and content needing review'):
            for warning in report['warnings']:
                st.text(warning)
