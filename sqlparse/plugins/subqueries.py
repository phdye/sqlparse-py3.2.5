from __future__ import absolute_import

import sqlparse
from sqlparse import plugins


class Subqueries(object):
    """Very small formatter for subquery placement."""

    def format(self, sql, options):
        open_same = options.get('open_paren_same_line', True)
        indent_width = int(options.get('indent_width', 2))
        cont_indent = int(options.get('continuation_indent', indent_width))
        body_indent_opt = options.get('body_indent', 2)
        align_under_open = False
        if isinstance(body_indent_opt, str):
            if body_indent_opt == 'plus_one':
                body_indent = indent_width + cont_indent
            elif body_indent_opt == 'under_open':
                body_indent = indent_width
                align_under_open = True
            else:
                body_indent = indent_width
        else:
            body_indent = int(body_indent_opt)
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
            line = before[nl + 1:] if nl != -1 else before
            stripped = line.lstrip(' ')
            return len(line) - len(stripped), len(line)

        positions = find_subqueries(sql)
        for start, end in reversed(positions):
            indent, open_pos = calc_indent(sql, start)
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

            inner_indent = open_pos + 1 if align_under_open else indent + body_indent

            if prefer_kw_newline:
                inner_text = '\n'.join(' ' * inner_indent + line for line in lines)
                replacement = open_part + '\n' + inner_text
            else:
                first = lines[0] if lines else ''
                rest = lines[1:] if len(lines) > 1 else []
                rest_text = '\n'.join(' ' * inner_indent + line for line in rest)
                replacement = open_part + ' ' + first
                if rest_text:
                    replacement += '\n' + rest_text

            if align_under_open:
                close_indent = open_pos if close_align else inner_indent
            else:
                close_indent = indent if close_align else inner_indent
            replacement += '\n' + ' ' * close_indent + ')'

            sql = before + replacement + after

        return sql


plugins.register_plugin('subqueries', Subqueries)
