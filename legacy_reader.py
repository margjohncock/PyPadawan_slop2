"""Conservative static packaging and configuration readers. Never evaluate code."""
import ast
import configparser
import re

from packaging.requirements import InvalidRequirement, Requirement

from source_reader import dotted, evidence


def setup_metadata(path, text):
    tree = ast.parse(text)
    values = {}

    def literal(node):
        if isinstance(node, ast.Name):
            return values.get(node.id)
        if isinstance(node, (ast.List, ast.Tuple)):
            return [literal(item) for item in node.elts]
        if isinstance(node, ast.Dict):
            return {literal(k): literal(v) for k, v in zip(node.keys, node.values)
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if isinstance(node, ast.Constant):
            return node.value
        return None

    aliases = {'setup', 'setuptools.setup', 'distutils.core.setup'}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in {'setuptools', 'distutils.core'}:
            aliases.update(a.asname or a.name for a in node.names if a.name == 'setup')
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = literal(node.value)
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if dotted(call.func) not in aliases:
            continue
        raw = {k.arg: literal(k.value) for k in call.keywords if k.arg}
        dependencies = raw.get('install_requires')
        scripts = {}
        entry = raw.get('entry_points')
        if isinstance(entry, dict) and isinstance(entry.get('console_scripts'), list):
            for item in entry['console_scripts']:
                if isinstance(item, str) and '=' in item:
                    name, target = item.split('=', 1)
                    scripts[name.strip()] = target.strip()
        details = {key: raw[key] for key in ('name', 'description') if isinstance(raw.get(key), str)}
        details['scripts'] = scripts
        details['dependencies'] = []
        details['unresolved'] = []
        if isinstance(raw.get('python_requires'), str):
            details['requires-python'] = raw['python_requires']
        if isinstance(dependencies, list):
            for item in dependencies:
                try:
                    if not isinstance(item, str):
                        raise ValueError('dynamic dependency')
                    details['dependencies'].append(str(Requirement(item)))
                except (InvalidRequirement, ValueError):
                    details['unresolved'].append('A dependency could not be read statically')
        else:
            details['unresolved'].append('install_requires is absent or dynamic')
        if raw.get('use_scm_version') or not isinstance(raw.get('version'), str):
            details['unresolved'].append('Package version is dynamic or absent')
        return {'path': path, 'kind': 'setup', 'at_root': '/' not in path,
                'usable': False, 'details': details,
                'evidence': evidence(path, text, call.lineno, call.end_lineno)}
    return None


def read_configuration(path, text):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read_string(text)
    result, section = [], ''
    # Read raw assignments for precise line evidence, including author comments.
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r'\s*\[([^]]+)\]', line)
        if match:
            section = match[1]
        elif section and re.match(r'\s*[^#;\s][^=:]*\s*[=:]', line):
            name = re.split('[=:]', line, maxsplit=1)[0].strip()
            if parser.has_option(section, name):
                result.append({'section': section, 'name': name,
                               'value': parser.get(section, name, raw=True),
                               'evidence': evidence(path, text, number)})
    return result


def dependency_differences(manifests):
    seen, differences = {}, []
    for manifest in manifests:
        if not manifest['at_root']:
            continue
        for item in manifest['details'].get('dependencies', []):
            if not isinstance(item, str):
                continue
            try:
                requirement = Requirement(item)
            except InvalidRequirement:
                continue
            key = re.sub('[-_.]+', '-', requirement.name).lower()
            current = (str(requirement.specifier) or 'no version constraint', manifest)
            previous = seen.get(key)
            if previous and previous[0] != current[0]:
                differences.append({'text': f"Different declarations for {key}: {previous[1]['path']} "
                                    f"has {previous[0]}; {manifest['path']} has {current[0]}. "
                                    'These have not been resolved or installation-tested.',
                                    'evidence': [previous[1]['evidence'], manifest['evidence']]})
            seen[key] = current
    return differences
