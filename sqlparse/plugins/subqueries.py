from __future__ import absolute_import

import sqlparse
from sqlparse import plugins


class Subqueries(object):
    """Very small formatter for subquery placement."""

    def format(self, sql, options):
        open_same = options.get('open_paren_same_line', True)
        body_indent = int(options.get('body_indent', 2))
        close_align = options.get('close_paren_align_with_open', True)
        prefer_kw_newline = options.get('prefer_keyword_on_newline', False)

        def find_subqueries(text):
            positions = []
            lower = text.lower()
            start = 0
            while True:
                idx = lower.find('(select', start)
                if idx == -1:
                    break
                depth = 1
                i = idx + 1
                length = len(text)
                while i < length:
                    ch = text[i]
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                        if depth == 0:
                            positions.append((idx, i))
                            break
                    i += 1
                start = i + 1
            return positions

        def calc_indent(text, pos):
            before = text[:pos]
            nl = before.rfind('\n')
            if nl == -1:
                return 0
            line = before[nl + 1:]
            stripped = line.lstrip(' ')
            return len(line) - len(stripped)

        positions = find_subqueries(sql)
        for start, end in reversed(positions):
            indent = calc_indent(sql, start)
            inner = sql[start + 1:end]
            formatted = sqlparse.format(inner.strip(), reindent=True,
                                        indent_width=body_indent)
            lines = [l.rstrip() for l in formatted.strip().splitlines()]
            before = sql[:start]
            after = sql[end + 1:]

            if open_same:
                before = before.rstrip() + ' '
                open_part = '('
            else:
                before = before.rstrip()
                open_part = '\n' + ' ' * indent + '('

            if prefer_kw_newline:
                inner_text = '\n'.join(' ' * (indent + body_indent) + line
                                        for line in lines)
                replacement = open_part + '\n' + inner_text
            else:
                first = lines[0] if lines else ''
                rest = lines[1:] if len(lines) > 1 else []
                rest_text = '\n'.join(' ' * (indent + body_indent) + line
                                       for line in rest)
                replacement = open_part + ' ' + first
                if rest_text:
                    replacement += '\n' + rest_text

            close_indent = indent if close_align else indent + body_indent
            replacement += '\n' + ' ' * close_indent + ')'

            sql = before + replacement + after

        return sql


plugins.register_plugin('subqueries', Subqueries)
