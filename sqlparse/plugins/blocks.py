from __future__ import print_function
import re
import sys
from sqlparse import plugins


class BlocksPlugin(object):
    """Formatter plugin for procedural blocks and declaration sections.

    This plugin implements a subset of the behaviour described in the
    configuration plan.  It operates on plain text for simplicity and is
    intentionally lightweight for compatibility with Python 3.2.5.
    """

    def format(self, stream, options):
        print(": sqlparse.plugins.blocks.format(...)", file=sys.stderr)
        text = stream
        if isinstance(stream, (list, tuple)):
            text = ''.join(stream)

        block_opts = options.get('blocks') or {}
        decl_opts = options.get('declarations') or {}

        if block_opts.get('begin_same_line'):
            text = re.sub(r'\n([ \t]*)BEGIN', r' BEGIN', text, flags=re.IGNORECASE)

        if block_opts.get('end_own_line'):
            # ensure END appears on its own line
            text = re.sub(r'\s*END', r'\nEND', text, flags=re.IGNORECASE)

        if block_opts.get('label_column') == 0:
            # move labels like <<label>> to column 0
            text = re.sub(r'^[ \t]+(<<[^>]+>>)', r'\1', text, flags=re.MULTILINE)

        if block_opts.get('align_end_with_opener'):
            text = _align_end_with_opener(text)

        if (decl_opts.get('one_per_line') or decl_opts.get('align_types') or
                decl_opts.get('align_assignment')):
            text = _format_declarations(text, decl_opts)

        return text


def _align_end_with_opener(text):
    ends_with_nl = text.endswith('\n')
    lines = text.splitlines()
    stack = []
    result = []
    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        upper = stripped.upper()
        if upper.startswith('BEGIN'):
            stack.append(indent)
        elif upper.startswith('END'):
            if stack:
                indent = stack.pop()
            stripped = stripped.lstrip()
            line = ' ' * indent + stripped
        result.append(line)
    joined = '\n'.join(result)
    if ends_with_nl:
        joined += '\n'
    return joined


def _format_declarations(text, options):
    m = re.search(r'\bDECLARE\b(.*?)(\bBEGIN\b)', text,
                  flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return text
    pre = text[:m.start(1)]
    if not pre.endswith('\n'):
        pre += '\n'
    decl_block = m.group(1)
    post = text[m.start(2):]

    indent_match = re.search(r'\n([ \t]*)', decl_block)
    if indent_match:
        indent = indent_match.group(1)
    else:
        indent = ''

    decl_block = decl_block.replace('\n', ' ')
    parts = [p.strip() for p in decl_block.split(';') if p.strip()]

    parsed = []
    max_name = 0
    max_type = 0
    for part in parts:
        tokens = re.split(r'(\s+)', part, 1)
        if len(tokens) >= 3:
            name = tokens[0]
            rest = tokens[2].strip()
        else:
            name = part
            rest = ''
        assign_split = re.split(r'(:=|=)', rest, 1)
        if len(assign_split) == 3:
            type_part = assign_split[0].rstrip()
            assign_op = assign_split[1]
            value_part = assign_split[2].lstrip()
        else:
            type_part = rest
            assign_op = ''
            value_part = ''
        parsed.append([name, type_part, assign_op, value_part])
        if options.get('align_types') and len(name) > max_name:
            max_name = len(name)
        if options.get('align_assignment') and len(type_part) > max_type:
            max_type = len(type_part)

    lines = []
    for name, type_part, assign_op, value_part in parsed:
        line = name
        if options.get('align_types'):
            line += ' ' * (max_name - len(name) + 1)
        else:
            line += ' '
        line += type_part
        if assign_op:
            if options.get('align_assignment'):
                line += ' ' * (max_type - len(type_part) + 1)
                line += assign_op + ' ' + value_part
            else:
                line += ' ' + assign_op + ' ' + value_part
        line += ';'
        lines.append(indent + line)

    formatted = '\n'.join(lines)
    return pre + formatted + '\n' + post


plugins.register_plugin('blocks', BlocksPlugin)
