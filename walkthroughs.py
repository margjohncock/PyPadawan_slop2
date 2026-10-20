"""Apply inert, versioned teaching guides only to their reviewed source bytes."""
import hashlib
from importlib.resources import files
from pathlib import PurePosixPath

import yaml

from source_reader import evidence, read_text

SECTIONS = {'purpose', 'inputs', 'reading', 'processing', 'running', 'success', 'settings'}


def source_digest(path):
    with path.open('rb') as stream:
        content = stream.read(20_000_001)
    if len(content) > 20_000_000:
        raise ValueError('Guide source exceeds 20 MB')
    return hashlib.sha256(content.replace(b'\r\n', b'\n')).hexdigest()


def project_file(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
        raise ValueError('Guide references an unsafe project path')
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f'Guide source is unavailable: {relative}')
    return target


def anchor_reference(root, anchor):
    relative = anchor['path']
    text = read_text(project_file(root, relative), limit=20_000_000)
    cell = anchor.get('cell')
    if cell is not None:
        import nbformat
        notebook = nbformat.reader.reads(text)
        source = notebook['cells'][cell - 1]['source']
        text = ''.join(source) if isinstance(source, list) else source
    needle = anchor['contains']
    position = text.find(needle)
    if position < 0:
        raise ValueError(f'Guide source anchor no longer matches: {relative}')
    start = text[:position].count('\n') + 1
    return evidence(relative, text, start, start + needle.count('\n'), cell)


def load_guides():
    guides = []
    for resource in sorted(files('pypadawan_guides').iterdir(), key=lambda item: item.name):
        if resource.name.endswith('.yml'):
            guide = yaml.safe_load(resource.read_text(encoding='utf-8'))
            if not isinstance(guide, dict) or guide.get('schema_version') != 1:
                raise ValueError('Unsupported bundled walkthrough')
            if set(guide['sections']) != SECTIONS or not guide.get('fingerprints'):
                raise ValueError('Walkthrough must define seven sections and source fingerprints')
            guides.append(guide)
    return guides


def apply_walkthroughs(root, data, by_path, report, build_example, enabled=True):
    report['walkthroughs'] = []
    if not enabled:
        report['walkthroughs'].append({'status': 'disabled', 'title': 'General inspection only'})
        return
    for guide in load_guides():
        checks = []
        for relative, expected in guide['fingerprints'].items():
            try:
                actual = source_digest(project_file(root, relative))
                checks.append(actual == expected)
            except (OSError, ValueError):
                checks.append(False)
        if not any(checks):
            continue
        status = {'id': guide['id'], 'title': guide['title'],
                  'revision': guide['revision'], 'url': guide['url'], 'status': 'needs_review'}
        report['walkthroughs'].append(status)
        if not all(checks):
            status['message'] = 'Some source files differ from the reviewed snapshot. The scientific walkthrough is withheld; general inspection remains available.'
            continue
        try:
            task = build_example(guide['example'], data, by_path)
            task['id'] = 'guide:' + guide['id']
            task['title'] = guide['title']
            task['reviewed'] = True
            for destination in task['sections']:
                cards = []
                for card in guide['sections'][destination['id']]:
                    refs = [anchor_reference(root, anchor) for anchor in card['anchors']]
                    cards.append({'text': card['text'], 'basis': 'reviewed', 'evidence': refs})
                destination['source_cards'] = destination['cards']
                destination['cards'] = cards
                if destination['id'] == 'reading':
                    refs = [anchor_reference(root, item) for item in guide['route']]
                    destination['route'] = [{'path': ref['path'], 'cell': ref['cell']} for ref in refs]
                    destination['definitions'] = []
                    destination['cards'].extend({'text': item['role'], 'basis': 'reviewed', 'evidence': [ref]}
                                                for item, ref in zip(guide['route'], refs))
                if destination['id'] == 'running':
                    destination['reviewed_recipe'] = guide['recipe']
                    destination['recipe_status'] = guide['recipe']['status']
                    # Avoid displaying unrelated automatic installation templates beside this lesson.
                    destination['installation_routes'] = []
                    destination['documented_commands'] = []
            report['examples'].insert(0, task)
            status['status'] = 'applied'
            status['message'] = 'Source matches the reviewed teaching snapshot. Commands have not been run by PyPadawan.'
        except (KeyError, OSError, ValueError, TypeError, IndexError) as error:
            status['message'] = str(error)
    if not report['walkthroughs']:
        report['walkthroughs'].append({'status': 'unavailable', 'title': 'General inspection',
                                      'message': 'No matching reviewed walkthrough is bundled. Source-based findings remain available.'})
