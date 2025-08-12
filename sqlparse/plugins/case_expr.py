from __future__ import unicode_literals

"""CASE expression formatting plugin."""

from sqlparse import parse
from sqlparse.sql import Case
from sqlparse import plugins
from sqlparse import tokens as T

try:
    unicode
except NameError:  # pragma: no cover - Py3
    unicode = str

try:
    basestring
except NameError:  # pragma: no cover - Py3
    basestring = str


class CaseExpressionFormatter(object):
    """Format CASE expressions according to configuration options.

    Supported options inside the ``case_expr`` section:

    ``indent_when_then`` -- indent WHEN/THEN/ELSE lines.
    ``align_then`` -- align THEN clauses across WHEN conditions.
    ``end_align_with_case`` -- align END with CASE keyword.
    """

    def format(self, stream, options):
        # Allow passing either the whole options dict or the case_expr section.
        case_opts = options.get('case_expr') if isinstance(options, dict) else None
        if case_opts is None:
            case_opts = options
        indent_width = case_opts.get('indent_width') or options.get('indent_width') or 2
        indent_char = case_opts.get('indent_char') or options.get('indent_char') or ' '
        indent = indent_char * indent_width

        indent_when_then = case_opts.get('indent_when_then')
        align_then = case_opts.get('align_then')
        end_align_with_case = case_opts.get('end_align_with_case')

        if isinstance(stream, basestring):
            text = stream
        else:
            text = ''.join(stream)

        statements = parse(text)
        for stmt in statements:
            for token in stmt.tokens:
                if isinstance(token, Case):
                    formatted = self._format_case(token, indent_when_then, align_then,
                                                  end_align_with_case, indent)
                    text = text.replace(str(token), formatted, 1)
        return text

    def _format_case(self, case, indent_when_then, align_then, end_align_with_case, indent):
        cases = case.get_cases(skip_ws=True)
        parts = []
        when_clauses = []
        else_clause = None
        max_when = 0
        for cond, val in cases:
            if cond is None:
                if val and val[0].match(T.Keyword, 'ELSE'):
                    val = val[1:]
                else_clause = ''.join([unicode(t) for t in val]).strip()
            else:
                if cond and cond[0].match(T.Keyword, 'WHEN'):
                    cond = cond[1:]
                if val and val[0].match(T.Keyword, 'THEN'):
                    val = val[1:]
                cond_str = ''.join([unicode(t) for t in cond]).strip()
                then_str = ''.join([unicode(t) for t in val]).strip()
                when_clauses.append((cond_str, then_str))
                if len(cond_str) > max_when:
                    max_when = len(cond_str)

        parts.append('CASE')
        for cond_str, then_str in when_clauses:
            line = 'WHEN ' + cond_str
            if align_then:
                pad = max_when - len(cond_str)
                if pad > 0:
                    line += ' ' * pad
            line += ' THEN ' + then_str
            if indent_when_then:
                line = indent + line
            parts.append(line)
        if else_clause is not None:
            line = 'ELSE ' + else_clause
            if indent_when_then:
                line = indent + line
            parts.append(line)
        end_line = 'END'
        if indent_when_then and not end_align_with_case:
            end_line = indent + end_line
        parts.append(end_line)
        return '\n'.join(parts)


plugins.register_plugin('case_expr', CaseExpressionFormatter)
