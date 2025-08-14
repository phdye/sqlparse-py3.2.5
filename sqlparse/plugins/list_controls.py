import re
import sys

from sqlparse import plugins


class ListControls(object):
    """Formatter plugin implementing list related options.

    The plugin operates on the fully formatted SQL string to keep the
    implementation straightforward.  Only a subset of the intended behaviour is
    implemented which is sufficient for exercising the configuration surface.
    """

    def format(self, stream, options):
        print(": sqlparse.plugins.list_controls.format(...)", file=sys.stderr)
        sql = stream if isinstance(stream, str) else ''.join(stream)

        # bin_pack: collapse multi-line lists into a single line
        if options.get('bin_pack'):
            sql = re.sub(r',\s*\n\s*', ', ', sql)
            sql = re.sub(r'\(\s*\n\s*', '(', sql)

        # break_after_comma: place a newline after each comma
        if options.get('break_after_comma'):
            sql = re.sub(r',\s*', ',\n', sql)

        # align_after_open_paren: indent items after an opening parenthesis
        if options.get('align_after_open_paren'):
            sql = re.sub(r'\(\n', '(\n    ', sql)

        # trailing_comma_in_select: add or remove trailing comma before FROM
        if 'trailing_comma_in_select' in options:
            want = options['trailing_comma_in_select']
            pattern = re.compile(r'(SELECT\s+[^;]*?)(\s+FROM)', re.IGNORECASE | re.DOTALL)
            match = pattern.search(sql)
            if match:
                before, after = match.group(1), match.group(2)
                if want:
                    before = before.rstrip()
                    if not before.endswith(',') and ',' in before:
                        before += ','
                else:
                    before = re.sub(r',\s*$', '', before)
                sql = sql[:match.start(1)] + before + sql[match.end(1):]

        return sql


plugins.register_plugin('lists', ListControls)
