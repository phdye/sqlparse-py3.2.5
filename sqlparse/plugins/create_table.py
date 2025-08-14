import sys
from sqlparse import plugins


class CreateTablePlugin(object):
    """Formatter plugin for CREATE TABLE statements.

    Supports options from the ``create_table`` section:

    - align_columns: Align column definitions.
    - comma_last: Place commas at end of lines if True, else at start.
    - one_column_per_line: Put each column definition on its own line.
    """

    def format(self, stream, options):
        print(": sqlparse.plugins.create_table.format(...)", file=sys.stderr)
        if isinstance(stream, str):
            sql = stream
        else:
            sql = ''.join(stream)
        opts = {}
        if options:
            opts = options.get('create_table') or {}
        if 'CREATE TABLE' not in sql.upper():
            return sql
        try:
            prefix, rest = sql.split('(', 1)
            body, suffix = rest.rsplit(')', 1)
        except ValueError:
            return sql
        columns = []
        for part in body.split(','):
            columns.append(part.strip())
        align = bool(opts.get('align_columns'))
        comma_last = True
        if 'comma_last' in opts:
            comma_last = bool(opts.get('comma_last'))
        one_per_line = bool(opts.get('one_column_per_line'))
        if align:
            names = []
            for col in columns:
                parts = col.split(None, 1)
                if parts:
                    names.append(parts[0])
            max_len = 0
            for name in names:
                if len(name) > max_len:
                    max_len = len(name)
            aligned = []
            for col in columns:
                parts = col.split(None, 1)
                if len(parts) > 1:
                    name, restcol = parts[0], parts[1]
                    pad = ' ' * (max_len - len(name) + 1)
                    aligned.append(name + pad + restcol)
                else:
                    aligned.append(col)
            columns = aligned
        if one_per_line:
            lines = []
            for idx, col in enumerate(columns):
                if comma_last:
                    line = col
                    if idx != len(columns) - 1:
                        line += ','
                    lines.append(line)
                else:
                    if idx == 0:
                        lines.append(col)
                    else:
                        lines.append(', ' + col)
            body = '\n  '.join(lines)
            formatted = prefix.rstrip() + ' (\n  ' + body + '\n)' + suffix
        else:
            if comma_last:
                body = ', '.join(columns)
            else:
                if columns:
                    body = columns[0]
                    for col in columns[1:]:
                        body += ' , ' + col
                else:
                    body = ''
            formatted = prefix.rstrip() + ' (' + body + ')' + suffix
        return formatted


# Register plugin at import time
plugins.register_plugin('create_table', CreateTablePlugin)
