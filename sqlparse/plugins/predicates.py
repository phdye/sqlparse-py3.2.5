"""Predicate layout plugin."""

import re
import sys

from sqlparse import plugins


@plugins.register_plugin('predicates')
class PredicateLayout(object):
    """Handle predicate layout options.

    Supported options::

        predicates.layout: "compact", "one_per_line", or "heuristic"
    """

    def format(self, stream, options):
        print(": sqlparse.plugins.predicates.format(...)", file=sys.stderr)
        opts = options.get('predicates')
        if not isinstance(opts, dict):
            return stream

        layout = opts.get('layout')
        if layout not in ('compact', 'one_per_line', 'heuristic'):
            return stream
        if layout == 'compact':
            return stream

        indent_width = options.get('indent_width', 2)
        indent = ' ' * indent_width

        def apply_one_per_line(txt):
            txt = re.sub(r'(WHERE)\s+', 'WHERE\n' + indent, txt,
                         flags=re.IGNORECASE)
            txt = re.sub(r'\s+(AND|OR)\s+',
                         '\n' + indent + r'\1 ', txt,
                         flags=re.IGNORECASE)
            return txt

        text = stream
        if layout == 'one_per_line':
            return apply_one_per_line(text)

        # heuristic
        match = re.search(r'\bWHERE\b', text, flags=re.IGNORECASE)
        if match is None:
            return stream
        after = text[match.end():]
        bool_ops = re.findall(r'\b(AND|OR)\b', after, flags=re.IGNORECASE)
        if len(bool_ops) <= 1 and len(after.strip()) <= 40:
            return stream
        return apply_one_per_line(text)

