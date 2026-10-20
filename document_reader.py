"""Extract documentation structure without rendering HTML or building Sphinx."""
import io
import re

from docutils import nodes
from docutils.core import publish_doctree
from markdown_it import MarkdownIt

from source_reader import evidence

TOPICS = {
    'purpose': ('about', 'overview', 'introduction', 'purpose', 'summary'),
    'method': ('method', 'analysis', 'algorithm', 'workflow', 'processing', 'approach', 'protocol'),
    'inputs': ('input', 'data', 'format', 'unit', 'prepar', 'download', 'alignment', 'variant'),
    'run': ('install', 'usage', 'quick', 'start', 'example', 'running', 'run', 'invocation'),
    'outputs': ('output', 'result', 'expected'),
    'settings': ('setting', 'parameter', 'option', 'config', 'argument', 'tunable'),
}


def read_document(path, text, cell=None):
    lines = text.splitlines()
    headings, blocks = [], []
    if path.lower().endswith('.rst'):
        tree = publish_doctree(text, settings_overrides={
            'file_insertion_enabled': False, 'raw_enabled': False,
            '_disable_config': True, 'warning_stream': io.StringIO(),
            'halt_level': 6, 'report_level': 5, 'line_length_limit': 2000,
        })
        for title in tree.findall(nodes.title):
            # Docutils can omit a title's line number. Match the original title.
            line = title.line or next((i + 1 for i, value in enumerate(lines)
                                       if value.strip() == title.astext()), 1)
            headings.append((line - 1, title.astext()))
        for block in tree.findall(nodes.literal_block):
            start = max(0, (block.line or 1) - 1)
            blocks.append((start, block.astext()))
    else:
        tokens = MarkdownIt('commonmark', {'html': False}).parse(text)
        for index, token in enumerate(tokens):
            if token.type == 'heading_open' and token.map:
                headings.append((token.map[0], tokens[index + 1].content))
            elif token.type in {'fence', 'code_block'} and token.map:
                blocks.append((token.map[0], token.content))
    boundaries = [(0, '')] + headings + [(len(lines), '')]
    sections, commands = [], []
    for index, (start, heading) in enumerate(boundaries[:-1]):
        end = boundaries[index + 1][0]
        if end <= start:
            continue
        content = '\n'.join(lines[start:end]).strip()
        if content:
            topics = [key for key, words in TOPICS.items()
                      if any(word in heading.lower() for word in words)]
            sections.append({'heading': heading, 'text': content[:2400],
                             'topics': topics or (['purpose'] if not sections else []),
                             'evidence': evidence(path, text, start + 1, end, cell)})
    for start, block in blocks:
        for offset, line in enumerate(block.splitlines()):
            candidate = line.strip().removeprefix('$ ').removeprefix('> ')
            if not candidate or candidate.startswith(('#', '>>>', '...', '<')):
                continue
            if not re.match(r'[\w./\\-]+(?:\s|$)', candidate):
                continue
            # Locate the exact source, preserving evidence for indented RST blocks.
            number = next((i + 1 for i in range(start, min(len(lines), start + len(block.splitlines()) + 8))
                           if lines[i].strip() == line.strip()), start + offset + 1)
            commands.append({'command': candidate[:600],
                             'evidence': evidence(path, text, number, number, cell)})
    return sections[:100], commands[:100]
