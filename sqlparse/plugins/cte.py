from __future__ import absolute_import
import re
import sys

from sqlparse import plugins


@plugins.register_plugin('cte')
class CTEFormatter(object):
    """Formatter for common table expressions (CTEs).

    This plugin implements configuration options:
    - cte.one_per_line
    - cte.blank_line_between
    - cte.trailing_comma_style ("always" or "remove")

    The implementation is intentionally lightweight and operates on raw SQL
    strings to maintain compatibility with Python 3.2.5.
    """

    def format(self, sql, options):  # pragma: no cover - exercised via tests
        print(": sqlparse.plugins.cte.format(...)", file=sys.stderr)
        cte_opts = options.get('cte') or {}
        if not cte_opts:
            return sql

        one_per_line = cte_opts.get('one_per_line')
        blank_between = cte_opts.get('blank_line_between')
        comma_style = cte_opts.get('trailing_comma_style') or 'remove'
        indent_width = options.get('indent_width', 2)
        indent = ' ' * indent_width

        match = re.match(r'(?is)\s*WITH\s+(.*)\s+(SELECT.*)', sql)
        if not match:
            return sql
        cte_part = match.group(1).strip()
        rest = match.group(2)

        ctes = self._split_ctes(cte_part)
        lines = []
        for idx, cte in enumerate(ctes):
            cte = cte.strip().rstrip(',')
            add_comma = (idx < len(ctes) - 1) or comma_style == 'always'
            line = cte + (',' if add_comma else '')
            if one_per_line:
                line = indent + line
            lines.append(line)

        if one_per_line:
            separator = '\n\n' if blank_between else '\n'
            cte_section = 'WITH\n' + separator.join(lines) + '\n'
        else:
            cte_section = 'WITH ' + ' '.join(lines) + ' '

        return cte_section + rest

    def _split_ctes(self, part):
        parts = []
        level = 0
        start = 0
        for idx, ch in enumerate(part):
            if ch == '(':
                level += 1
            elif ch == ')':
                if level:
                    level -= 1
            elif ch == ',' and level == 0:
                pieces = part[start:idx].strip()
                if pieces:
                    parts.append(pieces)
                start = idx + 1
        last = part[start:].strip()
        if last:
            parts.append(last)
        return parts
