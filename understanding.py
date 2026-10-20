"""Build seven evidence-based sections for one example at a time. No network I/O."""
import re
from collections import deque
from pathlib import PurePosixPath

from project_readers import read_project_files

QUESTIONS = [
    ('purpose', 'What does this project do?'),
    ('inputs', 'Could I use my data with it?'),
    ('reading', 'Where should I start reading?'),
    ('processing', 'What happens to the data?'),
    ('running', 'How do I try one example?'),
    ('success', 'How will I know it worked?'),
    ('settings', 'What do the settings mean?'),
]


def is_test(path):
    p = PurePosixPath(path)
    return 'tests' in p.parts or p.name.startswith('test_') or p.name.endswith('_test.py')


def section(key, title):
    return {'id': key, 'title': title, 'cards': []}


def add(destination, text, basis='observed', refs=(), **extra):
    destination['cards'].append({'text': text, 'basis': basis, 'evidence': list(refs), **extra})


def local_links(sources):
    index, by_path = {}, {}
    for source in sources:
        by_path.setdefault(source['path'], []).append(source)
        if source['cell'] is not None:
            continue
        parts = list(PurePosixPath(source['path']).with_suffix('').parts)
        if parts[-1] == '__init__':
            parts.pop()
        names = ['.'.join(parts)]
        if parts and parts[0] == 'src':
            names.append('.'.join(parts[1:]))
        for name in names:
            index.setdefault(name, set()).add(source['path'])

    def matches(source, imported):
        module = imported['module']
        level = imported.get('level', 0)
        if level:
            package = list(PurePosixPath(source['path']).parent.parts)
            if level > len(package):
                return []
            package = package[:len(package) - level + 1]
            module = '.'.join(package + ([module] if module else []))
        candidates = [module] + [f'{module}.{name}'.strip('.') for name in imported.get('names', [])]
        targets = set()
        for candidate in candidates:
            found = index.get(candidate, set())
            if not found and not level:
                sibling = (PurePosixPath(source['path']).parent / (candidate.replace('.', '/') + '.py')).as_posix()
                found = {sibling} if sibling in by_path else set()
            if len(found) == 1:
                targets.update(found)
        return sorted(targets)

    for source in sources:
        source['local_imports'] = []
        for imported in source['imports']:
            for target in matches(source, imported):
                if target != source['path']:
                    source['local_imports'].append({'path': target, 'evidence': imported['evidence']})
        for call in source['calls']:
            binding = call['binding']
            locations = [source['path']]
            name = call['target']
            if binding:
                imported = dict(binding, names=[binding['symbol']] if binding['symbol'] else [])
                name = binding['symbol'] or call['tail'].split('.')[-1]
                # `import package.module; package.module.func()` needs the full module path.
                if not binding['symbol'] and '.' in call['tail']:
                    imported['module'] = binding['module'] + '.' + call['tail'].rsplit('.', 1)[0]
                locations = matches(source, imported)
            found = []
            for location in locations:
                for candidate in by_path.get(location, []):
                    for definition in candidate['definitions']:
                        allowed = {name}
                        scope = call['scope'].split('.')
                        if scope != ['<module>']:
                            for count in range(len(scope), 0, -1):
                                allowed.add('.'.join(scope[:count] + [name]))
                        if definition['name'] in allowed:
                            found.append({'path': location, 'name': definition['name'],
                                          'evidence': definition['evidence']})
            if len(found) == 1:
                call['definition'] = found[0]
    return by_path


def installation_steps(manifest, platform):
    """Commands for a few recognised root manifests; display-only."""
    windows = platform == 'windows'
    executable = '.\\.venv\\Scripts\\python.exe' if windows else '.venv/bin/python'
    if manifest['kind'] == 'environment':
        return [
            {'command': f"conda env create --name pypadawan-example --file {manifest['path']}",
             'explanation': 'Requires Conda installed. Creates an isolated environment from this YAML. Change the environment name if it already exists.'},
            {'command': 'conda activate pypadawan-example',
             'explanation': 'Selects that environment for the documented commands in this terminal.'},
        ]
    install = '-r requirements.txt' if manifest['kind'] == 'requirements' else '.'
    return [
        {'command': ('python' if windows else 'python3') + ' -m venv .venv',
         'explanation': 'Creates a separate .venv folder for this example’s Python packages.'},
        {'command': f'{executable} -m pip install {install}',
         'explanation': ('Uses that environment’s Python to install the listed packages. -r means “read this requirements file”.'
                         if install != '.' else 'Builds and installs the local package in that environment. The dot means the current project folder.')},
    ]


def explain_command(command):
    if re.search(r'\bpip\s+install\b', command):
        return 'Installs packages; review the named file or package before running it locally.'
    if command.startswith('cd '):
        return 'Changes the terminal’s current folder. Use the path to your extracted local copy.'
    if 'jupyter' in command:
        return 'Opens Jupyter. Select the project’s Python environment and read notebook cells before running them.'
    if 'streamlit' in command:
        return 'Starts the project’s Streamlit interface and prints a local browser address.'
    if re.match(r'python(?:3)?\s', command):
        return 'Asks Python to run the named file, or the module after -m. Following options provide values to that program; see the settings section.'
    return 'Command quoted from the author’s documentation. Its complete behaviour has not been checked.'


def command_mentions(command, path):
    """Match complete documented paths, never a shared basename substring."""
    tokens = [part.strip('\"\'').replace('\\', '/').removeprefix('./')
              for part in re.findall(r'\"[^\"]*\"|\'[^\']*\'|\S+', command)]
    if path in tokens:
        return True
    if '-m' in tokens:
        position = tokens.index('-m') + 1
        module_path = tokens[position].replace('.', '/') if position < len(tokens) else ''
        candidate = path.removeprefix('src/')
        return candidate in {module_path + '.py', module_path + '/__main__.py'}
    return False


def build_example(example_path, data, by_path):
    sources = data['sources']
    queue = deque(by_path[example_path])
    route, visited = [], set()
    while queue and len(route) < 5:
        source = queue.popleft()
        identity = (source['path'], source['cell'])
        if identity in visited:
            continue
        visited.add(identity)
        route.append(source)
        for link in source['local_imports']:
            queue.extend(by_path.get(link['path'], []))
    related_paths = {s['path'] for s in route}
    docs = [d for d in data['documents'] if
            PurePosixPath(d['evidence']['path']).parent == PurePosixPath('.') or
            d['evidence']['path'] in related_paths or
            PurePosixPath(d['evidence']['path']).parent == PurePosixPath(example_path).parent]
    sections = [section(*question) for question in QUESTIONS]
    purpose, inputs, reading, processing, running, success, settings = sections

    def documented(target, topic):
        found = [d for d in docs if topic in d['topics'] and d['text'].strip()]
        for item in found[:4]:
            add(target, item['text'], 'documented', [item['evidence']], heading=item['heading'])
        return bool(found)

    has_purpose = documented(purpose, 'purpose')
    has_method = documented(purpose, 'method')
    has_outputs = documented(purpose, 'outputs')
    for manifest in data['manifests']:
        if manifest['at_root'] and manifest['kind'] == 'pyproject' and manifest['details'].get('description'):
            add(purpose, manifest['details']['description'], 'documented', [manifest['evidence']], heading='Package description')
            has_purpose = True
    if not has_purpose:
        module_docs = [s for s in route if s['docstring']]
        for source in module_docs[:2]:
            add(purpose, source['docstring'], 'documented', [source['documentation'][0]['evidence']])
        if not module_docs:
            add(purpose, 'No project purpose was documented in the supported README, package description or module docstrings. Scientific purpose cannot be established from filenames.', 'unknown')
    if not has_method:
        add(purpose, 'No separate method/workflow section was found. The source observations in section 4 show supported operations, but do not establish the scientific method.', 'unknown')
    if not has_outputs:
        add(purpose, 'No expected-results section was found in the documentation. Section 6 distinguishes output-writing calls from reference results.', 'unknown')

    documented_inputs = documented(inputs, 'inputs')
    operations = [operation for source in route for operation in source['operations']]
    for operation in [o for o in operations if o['category'] == 'input'][:12]:
        location = operation['argument'] or 'location not supplied in this call'
        add(inputs, f"{operation['text']}: {location}. A non-literal path is chosen at runtime.",
            refs=[operation['evidence']], note=operation['note'])
    referenced = {o['literal_path'] for o in operations if o['literal_path']}
    relevant_text = '\n'.join(d['text'] for d in docs)
    tables = [t for t in data['tables'] if t['path'] in referenced or t['path'] in relevant_text
              or t['path'] in '\n'.join(s['default'] or '' for source in route for s in source['settings'])]
    for table in tables[:5]:
        add(inputs, f"Supplied sample {table['path']} has header fields: {', '.join(table['headers'])}.", refs=[table['evidence']])
    accesses = [access for source in route for access in source['accesses']]
    for access in accesses[:10]:
        add(inputs, f"The code accesses {access['name']!r} on {access['object']}. This may be a table column or a dictionary key; its type and units are unverified.", refs=[access['evidence']])
    if not documented_inputs:
        add(inputs, 'Input units, observation layout and preparation requirements were not found in an input/data documentation section. Observed accesses alone are not a complete input specification.', 'unknown')
    if not tables:
        add(inputs, 'No referenced readable CSV/TSV sample header was found. Excel and binary data formats are not inspected.', 'unknown')

    for source in route:
        reason = ('Notebook code cell; read in saved cell order, which is not proof of execution order.' if source['cell'] else
                  'Contains a conventional main guard: a possible direct-run starting point.' if source['main_guard'] else
                  'Connected by a local import, or selected as a source file for review.')
        add(reading, f"{source['path']}" + (f", cell {source['cell']}" if source['cell'] else '') + ': ' + reason,
            refs=[source.get('start', source['evidence'])], description=source['docstring'])
        for link in source['local_imports'][:5]:
            add(reading, f"This file imports code matched to {link['path']}.", refs=[link['evidence']], target=link['path'])
    reading['route'] = [{'path': s['path'], 'cell': s['cell']} for s in route]
    reading['definitions'] = []
    for source in route:
        for call in source['calls']:
            if 'definition' in call:
                target = call['definition']
                add(reading, f"{call['scope']} calls {target['name']} in {target['path']} (static match).",
                    refs=[call['evidence'], target['evidence']], target=target['path'], definition=target['name'])
    for source in route:
        for definition in source['definitions']:
            if len(reading['definitions']) < 12:
                reading['definitions'].append(definition)

    for operation in operations[:30]:
        add(processing, f"{operation['text']}" + (f" using {operation['argument']}" if operation['argument'] else '') + '.',
            refs=[operation['evidence']], note=operation['note'], scope=operation['scope'])
    definitions = reading['definitions']
    for definition in definitions[:8]:
        add(processing, f"{definition['signature']}: " + (definition['docstring'] or 'No purpose docstring was supplied.'),
            'documented' if definition['docstring'] else 'observed', [definition['evidence']],
            returns=definition['returns'])
    if not operations:
        add(processing, 'No supported data-processing patterns were recognised. Function definitions and source are available in section 3; the analysis has not inferred a research algorithm.', 'unknown')
    processing['notice'] = 'Operations are grouped by reading-route file and shown in source order within each file. They are not an execution trace. Branches, loops, decorators and dynamic calls can change behaviour.'

    documented(running, 'run')
    valid_names = {'requirements.txt', 'environment.yml', 'environment.yaml', 'pyproject.toml'}
    routes = [m for m in data['manifests'] if m['at_root'] and m['usable'] and m['path'] in valid_names]
    running['installation_routes'] = [dict(m, commands={p: installation_steps(m, p) for p in ('windows', 'posix')}) for m in routes]
    running['documented_commands'] = []
    filename = PurePosixPath(example_path).name
    for command in data['commands']:
        text = command['command']
        if command_mentions(text, example_path) and not re.search(r'\bpip\s+install\b', text):
            running['documented_commands'].append(dict(command, explanation=explain_command(text)))
    for manifest in data['manifests']:
        if manifest['at_root']:
            details = manifest['details']
            dependencies = details.get('dependencies', [])
            readable = [item if isinstance(item, str) else 'pip packages: ' + ', '.join(item.get('pip', []))
                        for item in dependencies]
            description = (f"{manifest['path']} declares: " + ', '.join(readable) if readable else
                           f"{manifest['path']} contains no direct dependency list for this reader.")
            if details.get('name'):
                description += ' Environment/project name: ' + details['name'] + '.'
            if details.get('unresolved'):
                description += ' Options, includes or direct URLs need manual review; they have not been followed.'
            add(running, description[:1600], refs=[manifest['evidence']], heading='Environment evidence')
            if details.get('requires-python'):
                add(running, 'Declared Python version constraint: ' + details['requires-python'], refs=[manifest['evidence']])
    if len(routes) > 1:
        add(running, 'Several supported root manifests exist. Choose a route after checking the documentation; no route is selected automatically.', 'unknown')
    if not routes:
        add(running, 'No fully supported root installation manifest was found. Review the documented installation instructions; imports have not been converted into guessed dependencies.', 'unknown')
    if not running['documented_commands']:
        add(running, f'No supported documented run command naming {filename} was found. This is a reading candidate, not a verified launch command. Review notebook instructions or ask the author for the missing command and arguments.', 'unknown')

    reference_output = documented(success, 'outputs')
    for operation in [o for o in operations if o['category'] in {'output', 'display', 'plot'}][:12]:
        add(success, f"The source contains a call that {operation['text'].lower()}" +
            (f" using {operation['argument']}" if operation['argument'] else '') + '. This is not a reference result or evidence of successful execution.',
            refs=[operation['evidence']], note=operation['note'])
    for saved in data['saved_outputs']:
        if saved['evidence']['path'] in related_paths:
            add(success, 'Saved notebook text output (not freshly executed):\n' + saved['text'], refs=[saved['evidence']])
            reference_output = True
    tests = [s for s in sources if is_test(s['path']) and PurePosixPath(s['path']).name != PurePosixPath(example_path).name]
    for test in tests[:2]:
        add(success, f"{test['path']} may provide examples of expected behaviour. The tests have not been run.", refs=[test['evidence']])
    if not reference_output:
        add(success, 'No documented reference result or saved notebook text output was found for comparison. A created file or a plausible figure alone does not establish correctness.', 'unknown')

    documented(settings, 'settings')
    for source in route:
        for setting in source['settings'][:30]:
            add(settings, f"{setting['name']} ({setting['kind']}); default: " +
                (setting['default'] if setting['default'] is not None else 'not explicitly declared') +
                ('. Description supplied by the author: ' + setting['help'] if setting['help'] else '. No explanation of its effect was supplied here.') +
                ('' if setting['supported'] else ' This declaration is dynamic or unsupported; review its source.'),
                refs=[setting['evidence']] + setting.get('uses', []), scope=setting['scope'],
                documented_help=setting['help'])
    if not any(s['settings'] for s in route):
        add(settings, 'No supported literal terminal options, function defaults or referenced constants were found along this reading route. Configuration may be constructed dynamically or defined elsewhere.', 'unknown')
    return {'id': example_path, 'path': example_path, 'sections': sections}


def build_understanding(root, paths):
    data = read_project_files(root, paths)
    by_path = local_links(data['sources'])
    docs = '\n'.join(d['text'] for d in data['documents'])

    def priority(path):
        filename = PurePosixPath(path).name
        documented = any(command_mentions(c['command'], path) for c in data['commands'])
        guards = any(s['main_guard'] for s in by_path[path])
        return (0 if documented else 1 if filename in docs else 2 if guards or path.endswith('.ipynb') else 3, path)

    candidates = sorted((p for p in by_path if not is_test(p) and PurePosixPath(p).name != '__init__.py'), key=priority)
    examples = [build_example(path, data, by_path) for path in candidates[:20]]
    warnings = data['warnings'] + [f"{s['path']}: {w}" for s in data['sources'] for w in s['warnings']]
    if len(candidates) > 20:
        warnings.append('Only the first 20 reading candidates are offered. Select a smaller project folder to explore the rest.')
    return {'schema_version': 1, 'examples': examples, 'files': data['files'],
            'warnings': warnings, 'questions': [dict(id=k, title=t) for k, t in QUESTIONS],
            'limitations': 'This local guide quotes documentation and extracts source facts. It does not infer undocumented scientific purpose, verify object types, solve dependencies or run the uploaded project.'}
