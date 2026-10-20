"""Bounded readers for documentation, manifests, sample headers and notebooks."""
import configparser
import csv
import io
import re
import tomllib

import nbformat
import yaml
from packaging.requirements import InvalidRequirement, Requirement

from document_reader import read_document
from legacy_reader import dependency_differences, read_configuration, setup_metadata
from source_reader import analyse_source, evidence, read_text


def safe_environment(text):
    depth = 0
    for count, event in enumerate(yaml.parse(text)):
        if isinstance(event, yaml.AliasEvent) or count > 10000:
            raise ValueError('YAML aliases and more than 10,000 parser events are unsupported')
        if isinstance(event, (yaml.SequenceStartEvent, yaml.MappingStartEvent)):
            depth += 1
        elif isinstance(event, (yaml.SequenceEndEvent, yaml.MappingEndEvent)):
            depth -= 1
        if depth > 50:
            raise ValueError('YAML nesting exceeds 50 levels')
    data = yaml.safe_load(text)
    if not isinstance(data, dict) or not isinstance(data.get('dependencies', []), list):
        raise ValueError('Expected an environment mapping with a dependencies list')
    for item in data.get('dependencies', []):
        if isinstance(item, str):
            continue
        if (not isinstance(item, dict) or set(item) != {'pip'} or not isinstance(item['pip'], list)
                or not all(isinstance(v, str) for v in item['pip'])):
            raise ValueError('Unsupported environment dependency structure')
    if not isinstance(data.get('channels', []), list) or not all(isinstance(v, str) for v in data.get('channels', [])):
        raise ValueError('Environment channels must be a list of strings')
    if data.get('name') is not None and not isinstance(data['name'], str):
        raise ValueError('Environment name must be text')
    return {key: data.get(key) for key in ('name', 'channels', 'dependencies')}


def read_project_files(root, paths):
    collected = {'sources': [], 'documents': [], 'commands': [], 'manifests': [],
                 'tables': [], 'saved_outputs': [], 'warnings': [], 'files': [],
                 'configurations': [], 'entry_points': [], 'discrepancies': []}
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        lower = path.name.lower()
        kind = ('python' if path.suffix == '.py' else
                'notebook' if path.suffix == '.ipynb' else
                'readme' if lower in {'readme', 'readme.md', 'readme.rst', 'readme.txt'}
                or path.suffix.lower() in {'.md', '.rst'} else
                'requirements' if lower == 'requirements.txt' else
                'environment' if lower in {'environment.yml', 'environment.yaml'} else
                'pyproject' if lower == 'pyproject.toml' else
                'configuration' if path.suffix.lower() in {'.conf', '.ini', '.cfg'} else
                'shell' if path.suffix.lower() in {'.sh', '.ps1', '.bat'} else
                'table' if path.suffix.lower() in {'.csv', '.tsv'} else None)
        if not kind:
            continue
        record = {'path': relative, 'kind': kind, 'status': 'readable'}
        collected['files'].append(record)
        try:
            if kind == 'table':
                with path.open('rb') as stream:
                    text = stream.read(64000).decode('utf-8-sig')
            else:
                text = read_text(path, limit=20_000_000 if kind == 'notebook' else 1_000_000)
            ref = evidence(relative, text, 1, min(20, len(text.splitlines())))
            if kind == 'python':
                collected['sources'].append(analyse_source(relative, text))
                if lower == 'setup.py':
                    manifest = setup_metadata(relative, text)
                    if manifest:
                        collected['manifests'].append(manifest)
            elif kind == 'readme':
                sections, commands = read_document(relative, text)
                collected['documents'].extend(sections)
                collected['commands'].extend(commands)
            elif kind == 'table':
                header = next(csv.reader(io.StringIO(text[:64000]), delimiter='\t' if path.suffix.lower() == '.tsv' else ','), [])
                collected['tables'].append({'path': relative, 'headers': [v[:200] for v in header[:50]],
                                             'evidence': evidence(relative, text, 1)})
            elif kind == 'configuration':
                collected['configurations'].append({'path': relative,
                    'values': read_configuration(relative, text), 'evidence': ref})
            elif kind == 'shell':
                for number, line in enumerate(text.splitlines(), 1):
                    value = line.strip()
                    if value and not value.startswith('#'):
                        collected['commands'].append({'command': value[:600],
                            'evidence': evidence(relative, text, number)})
            elif kind == 'notebook':
                # Keep partial notebooks inspectable; validate each supported shape below.
                notebook = nbformat.from_dict(nbformat.reader.parse_json(text))
                if not isinstance(notebook, dict) or notebook.get('nbformat') != 4 or not isinstance(notebook.get('cells'), list):
                    raise ValueError('Expected a format 4 notebook with a cells list')
                metadata = notebook.get('metadata', {})
                if not isinstance(metadata, dict) or not isinstance(metadata.get('kernelspec', {}), dict):
                    raise ValueError('Invalid notebook kernel metadata')
                language = metadata.get('kernelspec', {}).get('language', 'python')
                if not isinstance(language, str):
                    raise ValueError('Invalid notebook language')
                for number, cell in enumerate(notebook['cells'][:100], 1):
                    if not isinstance(cell, dict):
                        raise ValueError('Invalid notebook cell')
                    source = cell.get('source', '')
                    if isinstance(source, list) and all(isinstance(s, str) for s in source):
                        source = ''.join(source)
                    if not isinstance(source, str):
                        raise ValueError('Notebook cell source must be text')
                    if cell.get('cell_type') == 'markdown':
                        sections, commands = read_document(relative, source, number)
                        collected['documents'].extend(sections)
                        collected['commands'].extend(commands)
                    elif cell.get('cell_type') == 'code':
                        magic = any(line.lstrip().startswith(('%', '!', '?')) for line in source.splitlines())
                        if language.lower() != 'python' or source.lstrip().startswith('%%'):
                            collected['warnings'].append(f'{relative}, cell {number}: non-Python source or notebook magic not analysed')
                        else:
                            try:
                                cleaned = '\n'.join('' if line.lstrip().startswith(('%', '!', '?')) else line
                                                    for line in source.splitlines())
                                if magic:
                                    collected['warnings'].append(f'{relative}, cell {number}: notebook magic lines omitted; other Python source inspected')
                                analysed = analyse_source(relative, cleaned, number)
                                # Restore original excerpts after line-preserving magic removal.
                                def restore(value):
                                    if isinstance(value, dict):
                                        if 'excerpt' in value and 'line_start' in value:
                                            value.update(evidence(relative, source, value['line_start'], value['line_end'], number))
                                        else:
                                            for child in value.values():
                                                restore(child)
                                    elif isinstance(value, list):
                                        for child in value:
                                            restore(child)
                                restore(analysed)
                                collected['sources'].append(analysed)
                            except (SyntaxError, ValueError, RecursionError) as error:
                                collected['warnings'].append(f'{relative}, cell {number}: {str(error)[:200]}')
                        outputs = cell.get('outputs', [])
                        if not isinstance(outputs, list):
                            raise ValueError('Notebook outputs must be a list')
                        for output in outputs[:3]:
                            if not isinstance(output, dict):
                                continue
                            data = output.get('data', {})
                            stored = output.get('text', data.get('text/plain', '') if isinstance(data, dict) else '')
                            if isinstance(stored, list) and all(isinstance(v, str) for v in stored):
                                stored = ''.join(stored)
                            if isinstance(stored, str) and stored:
                                collected['saved_outputs'].append({'text': stored[:600], 'evidence': evidence(relative, source, 1, 5, number)})
                if len(notebook['cells']) > 100:
                    collected['warnings'].append(f'{relative}: only the first 100 cells were inspected')
            else:
                manifest = {'path': relative, 'kind': kind, 'at_root': path.parent == root,
                            'evidence': ref, 'usable': True, 'details': {}}
                if kind == 'requirements':
                    requirements, unresolved = [], []
                    for line in text.splitlines():
                        stripped = line.strip()
                        if not stripped or stripped.startswith('#'):
                            continue
                        try:
                            requirement = Requirement(stripped.split(' #', 1)[0])
                            requirements.append(str(requirement))
                            if requirement.url:
                                unresolved.append('Direct URL not fetched or verified')
                        except InvalidRequirement:
                            unresolved.append(stripped[:150])
                    manifest['usable'] = not unresolved
                    manifest['details'] = {'dependencies': requirements, 'unresolved': unresolved}
                elif kind == 'environment':
                    manifest['details'] = safe_environment(text)
                else:
                    data = tomllib.loads(text)
                    project, build = data.get('project', {}), data.get('build-system', {})
                    if not isinstance(project, dict) or not isinstance(build, dict):
                        raise ValueError('Project/build-system must be TOML tables')
                    for key in ('name', 'description', 'requires-python'):
                        if project.get(key) is not None and not isinstance(project[key], str):
                            raise ValueError(f'Project {key} must be text')
                    dependencies = project.get('dependencies', [])
                    scripts = project.get('scripts', {})
                    if not isinstance(dependencies, list) or not all(isinstance(v, str) for v in dependencies):
                        raise ValueError('Project dependencies must be a list of strings')
                    for requirement in dependencies:
                        Requirement(requirement)
                    if not isinstance(scripts, dict) or not all(isinstance(v, str) for v in scripts.values()):
                        raise ValueError('Project scripts must be a mapping of names to text')
                    manifest['details'] = {**project, 'build-system': build}
                    manifest['usable'] = bool(project.get('name') and build.get('requires') and build.get('build-backend'))
                collected['manifests'].append(manifest)
                if not manifest['usable']:
                    collected['warnings'].append(f'{relative}: incomplete or unsupported installation content; review manually')
        except (OSError, UnicodeError, ValueError, TypeError, SyntaxError, RecursionError, yaml.YAMLError,
                nbformat.reader.NotJSONError, configparser.Error, AttributeError) as error:
            record['status'] = 'unreadable'
            collected['warnings'].append(f'{relative}: {str(error)[:300]}')
    for manifest in collected['manifests']:
        for name, target in manifest['details'].get('scripts', {}).items():
            module, _, function = target.partition(':')
            candidates = [module.replace('.', '/') + '.py', module.replace('.', '/') + '/__init__.py']
            found = next((prefix + candidate for prefix in ('', 'src/') for candidate in candidates
                          if any(s['path'] == prefix + candidate for s in collected['sources'])), None)
            collected['entry_points'].append({'name': name, 'target': target, 'path': found,
                'function': function, 'evidence': manifest['evidence']})
    collected['discrepancies'].extend(dependency_differences(collected['manifests']))
    for command in collected['commands']:
        match = re.match(r'python(?:3(?:\.\d+)?)?\s+[\"\']?([^\s\"\']+\.py)', command['command'])
        if match:
            origin = root / command['evidence']['path']
            base = origin.parent if origin.suffix in {'.sh', '.ps1', '.bat'} else root
            target = (base / match[1]).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                collected['discrepancies'].append({'text': f"Documented command references a missing or outside-project script: {match[1]}. Review the working folder and current entry point.",
                    'evidence': [command['evidence']]})
    return collected
