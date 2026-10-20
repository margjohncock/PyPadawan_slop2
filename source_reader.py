"""Read source facts for a beginner's walkthrough without loading project modules."""
import ast

MAX_SOURCE_BYTES = 1_000_000


def read_text(path):
    with path.open('rb') as stream:
        content = stream.read(MAX_SOURCE_BYTES + 1)
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError('File exceeds the 1 MB inspection limit')
    return content.decode('utf-8-sig')


def evidence(path, text, start=1, end=None, cell=None):
    lines = text.splitlines() or ['']
    start = max(1, min(start, len(lines)))
    end = max(start, min(end or start, len(lines)))
    return {'path': path, 'line_start': start, 'line_end': end, 'cell': cell,
            'excerpt': '\n'.join(lines[start - 1:min(end, start + 19)])[:1800]}


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return f'{prefix}.{node.attr}' if prefix else f'.{node.attr}'
    return ''


def main_guard(node):
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    test = node.test
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    pair = [test.left, test.comparators[0]]
    return (any(isinstance(n, ast.Name) and n.id == '__name__' for n in pair)
            and any(isinstance(n, ast.Constant) and n.value == '__main__' for n in pair))


LIBRARY_ACTIONS = {
    'pandas.read_csv': ('input', 'Reads a CSV table'),
    'pandas.read_table': ('input', 'Reads a delimited table'),
    'pandas.read_excel': ('input', 'Reads an Excel workbook'),
    'pandas.read_json': ('input', 'Reads JSON into a table'),
    'numpy.load': ('input', 'Loads a NumPy array or archive'),
    'numpy.loadtxt': ('input', 'Reads numbers from text'),
    'numpy.genfromtxt': ('input', 'Reads a numeric table from text'),
    'numpy.mean': ('summary', 'Calculates an average'),
    'numpy.median': ('summary', 'Calculates a median'),
    'numpy.std': ('summary', 'Calculates a standard deviation'),
    'pandas.concat': ('transform', 'Combines tables'),
    'pandas.merge': ('transform', 'Joins tables'),
    'json.load': ('input', 'Reads JSON from a file object'),
    'json.dump': ('output', 'Writes JSON to a file object'),
    'matplotlib.pyplot.plot': ('plot', 'Draws a line plot'),
    'matplotlib.pyplot.scatter': ('plot', 'Draws a scatter plot'),
    'matplotlib.pyplot.savefig': ('output', 'Saves a figure'),
    'matplotlib.pyplot.show': ('plot', 'Displays a figure'),
    'print': ('display', 'Displays values in the terminal'),
    'input': ('input', 'Asks the person running the program for text'),
    'sum': ('summary', 'Adds a collection of values'),
    'len': ('summary', 'Counts items'),
}
METHOD_ACTIONS = {
    'dropna': ('transform', 'Removes missing values'),
    'fillna': ('transform', 'Replaces missing values'),
    'groupby': ('transform', 'Groups rows by matching values'),
    'mean': ('summary', 'Calculates an average'),
    'median': ('summary', 'Calculates a median'),
    'std': ('summary', 'Calculates a standard deviation'),
    'to_csv': ('output', 'Writes a table to CSV'),
    'to_excel': ('output', 'Writes a table to an Excel workbook'),
    'savefig': ('output', 'Saves a figure'),
    'read_text': ('input', 'Reads text from a file'),
    'read_bytes': ('input', 'Reads bytes from a file'),
    'write_text': ('output', 'Writes text to a file'),
    'write_bytes': ('output', 'Writes bytes to a file'),
}


def analyse_source(path, text, cell=None):
    tree = ast.parse(text)
    aliases = {}
    result = {'path': path, 'cell': cell, 'documentation': [], 'definitions': [],
              'imports': [], 'calls': [], 'operations': [], 'accesses': [],
              'settings': [], 'main_guard': False, 'warnings': [],
              'evidence': evidence(path, text, 1, 15, cell)}

    def ref(node):
        return evidence(path, text, node.lineno, node.end_lineno, cell)

    def expr(node):
        return ast.unparse(node)[:250] if node is not None else 'None'

    def doc(node, scope):
        description = ast.get_docstring(node)
        if description:
            result['documentation'].append({'scope': scope, 'text': description[:2000],
                                             'evidence': ref(node.body[0])})
        return (description or '')[:2000]

    result['docstring'] = doc(tree, '<module>')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split('.')[0]
                aliases[local] = {'module': alias.name if alias.asname else local, 'symbol': ''}
                result['imports'].append({'module': alias.name, 'level': 0, 'names': [], 'evidence': ref(node)})
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases[alias.asname or alias.name] = {'module': node.module or '', 'symbol': alias.name,
                                                      'level': node.level}
            result['imports'].append({'module': node.module or '', 'level': node.level,
                                      'names': [a.name for a in node.names], 'evidence': ref(node)})

    parsers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            target = dotted(node.value.func)
            head, _, tail = target.partition('.')
            binding = aliases.get(head, {})
            resolved = '.'.join(p for p in (binding.get('module', head), binding.get('symbol', ''), tail) if p)
            if resolved == 'argparse.ArgumentParser':
                parsers.update(t.id for t in node.targets if isinstance(t, ast.Name))

    class Reader(ast.NodeVisitor):
        def __init__(self):
            self.scope = []

        def definition(self, node, kind):
            name = '.'.join(self.scope + [node.name])
            parameters = []
            if kind != 'class':
                args = node.args
                positional = args.posonlyargs + args.args
                defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
                for arg, default in list(zip(positional, defaults)) + list(zip(args.kwonlyargs, args.kw_defaults)):
                    parameters.append({'name': arg.arg, 'default': expr(default) if default is not None else None})
                if args.vararg:
                    parameters.append({'name': '*' + args.vararg.arg, 'default': None})
                if args.kwarg:
                    parameters.append({'name': '**' + args.kwarg.arg, 'default': None})
            if len(result['definitions']) < 60:
                result['definitions'].append({'name': name, 'kind': kind,
                    'signature': f'{node.name}({ast.unparse(node.args)[:500]})' if kind != 'class' else node.name,
                    'parameters': parameters, 'docstring': doc(node, name), 'returns': [], 'evidence': ref(node)})
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node):
            self.definition(node, 'function')

        def visit_AsyncFunctionDef(self, node):
            self.definition(node, 'async function')

        def visit_ClassDef(self, node):
            self.definition(node, 'class')

        def visit_If(self, node):
            if not self.scope and main_guard(node):
                result['main_guard'] = True
                result['start'] = ref(node)
            self.generic_visit(node)

        def visit_Return(self, node):
            scope = '.'.join(self.scope)
            for definition in result['definitions']:
                if definition['name'] == scope and len(definition['returns']) < 5:
                    definition['returns'].append({'expression': expr(node.value), 'evidence': ref(node)})
            self.generic_visit(node)

        def visit_Subscript(self, node):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                if len(result['accesses']) < 100:
                    result['accesses'].append({'name': node.slice.value[:150],
                        'object': expr(node.value), 'scope': '.'.join(self.scope) or '<module>', 'evidence': ref(node)})
            self.generic_visit(node)

        def visit_Call(self, node):
            # For a chain such as frame.groupby(...).mean(), visit the inner
            # written operation first. This remains a reading aid, not a trace.
            self.generic_visit(node)
            if len(result['calls']) >= 200:
                return
            target = dotted(node.func)
            head, _, tail = target.partition('.')
            binding = aliases.get(head)
            resolved = target
            if binding and not binding.get('level'):
                resolved = '.'.join(p for p in (binding['module'], binding['symbol'], tail) if p)
            scope = '.'.join(self.scope) or '<module>'
            call = {'target': target or '<computed callable>', 'scope': scope,
                    'binding': binding, 'tail': tail, 'evidence': ref(node)}
            result['calls'].append(call)
            action = LIBRARY_ACTIONS.get(resolved)
            note = 'Matched by the written call name; imports or names may be rebound at runtime.'
            if not action and isinstance(node.func, ast.Attribute):
                action = METHOD_ACTIONS.get(node.func.attr)
                note = 'Method-name clue: the usual meaning is shown; the object type has not been checked.'
            if target == 'open':
                mode = next((kw.value for kw in node.keywords if kw.arg == 'mode'), node.args[1] if len(node.args) > 1 else None)
                if mode is None:
                    action = ('input', 'Opens a file for reading')
                elif isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                    action = ('output', 'Opens a file for writing or updating') if any(c in mode.value for c in 'wax+') else ('input', 'Opens a file for reading')
                else:
                    action = ('file', 'Opens a file using a mode determined elsewhere')
                note = 'Observed open call; the actual filename and object behaviour can depend on runtime values.'
            if action:
                argument = node.args[0] if node.args else next((k.value for k in node.keywords
                    if k.arg in {'filepath_or_buffer', 'path_or_buf', 'path', 'fname', 'file', 'io'}), None)
                if resolved == 'json.dump':
                    argument = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == 'fp'), None)
                if isinstance(node.func, ast.Attribute) and node.func.attr in {'read_text', 'read_bytes', 'write_text', 'write_bytes'}:
                    receiver = node.func.value
                    argument = receiver.args[0] if isinstance(receiver, ast.Call) and receiver.args else receiver
                result['operations'].append({'category': action[0], 'text': action[1],
                    'argument': expr(argument) if argument is not None else None,
                    'literal_path': argument.value if isinstance(argument, ast.Constant) and isinstance(argument.value, str) else None,
                    'scope': scope, 'note': note, 'evidence': ref(node)})
            if isinstance(node.func, ast.Attribute) and node.func.attr in {'groupby', 'dropna'}:
                fields = list(node.args[:1]) if node.func.attr == 'groupby' else []
                fields.extend(k.value for k in node.keywords if k.arg in {'by', 'subset'})
                for field in fields:
                    values = field.elts if isinstance(field, (ast.List, ast.Tuple)) else [field]
                    for value in values:
                        if isinstance(value, ast.Constant) and isinstance(value.value, str) and len(result['accesses']) < 100:
                            result['accesses'].append({'name': value.value[:150], 'object': expr(node.func.value),
                                'scope': scope, 'evidence': ref(node)})
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                literal_flags = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                kwargs = {k.arg: k.value for k in node.keywords}
                default = kwargs.get('default')
                help_node = kwargs.get('help')
                supported = (len(literal_flags) == len(node.args) and bool(literal_flags)
                             and isinstance(node.func.value, ast.Name) and node.func.value.id in parsers)
                if default is not None:
                    try:
                        ast.literal_eval(default)
                    except (ValueError, TypeError):
                        supported = False
                result['settings'].append({'kind': 'terminal option', 'name': ', '.join(literal_flags) or expr(node),
                    'default': expr(default) if default is not None else None,
                    'help': help_node.value if isinstance(help_node, ast.Constant) and isinstance(help_node.value, str) else None,
                    'supported': supported, 'scope': scope, 'evidence': ref(node)})

    Reader().visit(tree)
    loaded = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in loaded and len(loaded[node.id]) < 5:
                loaded[node.id].append(ref(node))
            elif node.id not in loaded and len(loaded) < 500:
                loaded[node.id] = [ref(node)]
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper() and target.id in loaded:
                    result['settings'].append({'kind': 'referenced constant', 'name': target.id,
                        'default': expr(node.value), 'help': None, 'supported': True,
                        'uses': loaded[target.id][:5], 'scope': '<module>', 'evidence': ref(node)})
    for definition in result['definitions']:
        for parameter in definition['parameters']:
            if parameter['default'] is not None:
                result['settings'].append({'kind': 'function default',
                    'name': f"{definition['name']}.{parameter['name']}", 'default': parameter['default'],
                    'help': definition['docstring'] or None, 'supported': True,
                    'scope': definition['name'], 'evidence': definition['evidence']})
    result['operations'].sort(key=lambda item: item['evidence']['line_start'])
    result['calls'].sort(key=lambda item: item['evidence']['line_start'])
    if sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in ast.walk(tree)) > 60:
        result['warnings'].append('Only the first 60 definitions are shown.')
    if sum(isinstance(n, ast.Call) for n in ast.walk(tree)) > 200:
        result['warnings'].append('Only the first 200 calls are analysed.')
    return result
