from __future__ import absolute_import

import sqlparse
from sqlparse import plugins


class SubqueriesPlugin(object):
    """Formatter plugin to handle subquery placement."""

    def format(self, stream, options):
        """Run the plugin on *stream* using *options*.

        The plugin only operates on :class:`Statement` instances during
        postprocessing. For other stream types the input is returned
        unchanged.
        """
        if stream is None:
            return stream
        sub_opts = options.get('subqueries') or {}
        if hasattr(stream, 'token_next'):
            return self._postprocess(stream, sub_opts, options)
        return stream

    def _postprocess(self, stmt, sub_opts, options):
        open_same = sub_opts.get('open_paren_same_line', True)
        body_indent_opt = sub_opts.get('body_indent', 2)
        if isinstance(body_indent_opt, str):
            opt = body_indent_opt.lower()
            if opt == 'plus_one':
                body_indent = options.get('indent_width', 2)
            elif opt == 'under_open':
                body_indent = 0
            else:
                try:
                    body_indent = int(body_indent_opt)
                except Exception:
                    body_indent = options.get('indent_width', 2)
        else:
            body_indent = int(body_indent_opt)
        close_align = sub_opts.get('close_paren_align_with_open', True)
        prefer_kw_newline = sub_opts.get('prefer_keyword_on_newline', False)

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

        sql = str(stmt)
        positions = find_subqueries(sql)
        for start, end in reversed(positions):
            inner = sql[start + 1:end]
            before = sql[:start]
            after = sql[end + 1:]
            if open_same:
                before_r = before.rstrip()
                indent = calc_indent(before_r, len(before_r))
                before = before_r + ' '
                open_part = '('
            else:
                indent = calc_indent(sql, start)
                before = before.rstrip()
                open_part = '\n' + ' ' * indent + '('
            formatted = sqlparse.format(inner.strip(), reindent=True,
                                        indent_width=body_indent)
            lines = [l.rstrip() for l in formatted.strip().splitlines()]

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

        return sqlparse.parse(sql)[0]


plugins.register_plugin('subqueries', SubqueriesPlugin)

