import re
import warnings

import sqlparse
from sqlparse import plugins


class DeclareCursorPlugin(object):
    """Formatter plugin implementing DECLARE CURSOR configuration options."""

    def format(self, stream, options):
        """Format *stream* according to declare_cursor options.

        EXEC SQL DECLARE [AT <db-alias>] CURSOR <cursor-name> FOR <query>;

        *stream* may be a SQL string. *options* is expected to contain a
        ``declare_cursor`` dictionary with the keys ``break_before``
    
        Default behavior is to format the DECLARE CURSOR statement as follows:
          EXEC SQL [AT <db-alias>] DECLARE CURSOR <cursor-name> FOR
              <query>;

        If ``break_before`` is True, the statement is formatted as:
          EXEC SQL [AT <db-alias>]
              DECLARE CURSOR <cursor-name> FOR
                  <query>;

        """
        if stream is None:
            return stream

        text = stream
        options = options.get('declare_cursor') or {}
        break_before = bool(options.get('break_before'))

        formatted = sqlparse.format(text, reindent=True)
        if not break_before:
            return formatted

        lines = formatted.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            lower = stripped.lower()
            if re.search(r'\bdeclare cursor\b', lower):
                stmt_indent = len(line) - len(stripped)
                for_match = re.search(r'\bfor\b', line, re.IGNORECASE)
                if not for_match:
                    warnings.warn("No 'FOR' clause found on DECLARE CURSOR statement line.", UserWarning)
                    return formatted
                declare_part = line[:for_match.end()].rstrip()
                if len(line) <= len(declare_part):
                    return formatted
                query_part = line[for_match.end()+1:].lstrip()
                indent = stmt_indent + 4
                lines[i] = declare_part
                lines.insert(i + 1, ' ' * indent + query_part)
                i += 1
            i += 1
        return '\n'.join(lines)

plugins.register_plugin('declare_cursor', DeclareCursorPlugin)
