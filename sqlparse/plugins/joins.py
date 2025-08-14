import re
import warnings
import sys

import sqlparse
from sqlparse import plugins


class JoinPlugin(object):
    """Formatter plugin implementing join configuration options."""

    def format(self, stream, options):
        """Format *stream* according to join options.

        *stream* may be a SQL string. *options* is expected to contain a
        ``joins`` dictionary with the keys ``join_on_new_line``,
        ``align_on_under_join`` and ``prefer_explicit``.
        """
        print(": sqlparse.plugins.joins.format(...)", file=sys.stderr)
        if stream is None:
            return stream

        text = stream
        join_opts = options.get('joins') or {}
        join_on_new_line = bool(join_opts.get('join_on_new_line'))
        align_on_under_join = bool(join_opts.get('align_on_under_join'))
        prefer_explicit = bool(join_opts.get('prefer_explicit'))

        if prefer_explicit:
            if re.search(r'\bfrom\b[^;]*,[^;]*', text, re.I):
                warnings.warn('comma join detected', UserWarning)

        formatted = sqlparse.format(text, reindent=True)
        lines = formatted.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            lower = stripped.lower()
            if re.search(r'\bjoin\b', lower):
                join_indent = len(line) - len(stripped)
                on_match = re.search(r'\bON\b', line, re.I)
                if on_match:
                    if join_on_new_line:
                        join_part = line[:on_match.start()].rstrip()
                        on_part = line[on_match.start():].lstrip()
                        indent = join_indent if align_on_under_join else join_indent + 2
                        lines[i] = join_part
                        lines.insert(i + 1, ' ' * indent + on_part)
                        i += 2
                        continue
                else:
                    if not join_on_new_line and i > 0:
                        prev = lines[i - 1].rstrip()
                        lines[i - 1] = prev + ' ' + stripped
                        lines.pop(i)
                        if i < len(lines) and lines[i].lstrip().lower().startswith('on '):
                            if align_on_under_join:
                                join_pos = lines[i - 1].lower().find('join')
                                lines[i] = ' ' * join_pos + lines[i].lstrip()
                        continue
                if align_on_under_join and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.lstrip().lower().startswith('on '):
                        lines[i + 1] = ' ' * (join_indent if align_on_under_join else join_indent + 2) + next_line.lstrip()
            i += 1
        return '\n'.join(lines)


plugins.register_plugin('joins', JoinPlugin)
