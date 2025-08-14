from __future__ import print_function
import re
import sys

from sqlparse import plugins


class CommentFormatter(object):
    """Formatter plugin to handle comment related options.

    The formatter operates on plain SQL strings for simplicity. It supports
    several options passed in the *options* dictionary under the ``comments``
    key:

    ``reflow_block_comments``
        Collapse consecutive whitespace inside block comments.

    ``keep_trailing_line_comment_with_code``
        If ``False`` move trailing line comments onto their own line.

    ``pragma_freeze_directives``
        Honour ``-- sqlparse: off`` / ``-- sqlparse: on`` regions which are
        left untouched by the formatter.

    ``preserve_comment_position``
        When ``True`` no positional changes to comments are made.
    """

    def format(self, sql, options):
        print(": sqlparse.plugins.comments.format(...)", file=sys.stderr)
        opts = options or {}
        if 'comments' in opts:
            opts = opts.get('comments') or {}

        reflow = bool(opts.get('reflow_block_comments'))
        keep_trailing = opts.get('keep_trailing_line_comment_with_code', True)
        freeze = bool(opts.get('pragma_freeze_directives'))
        preserve = bool(opts.get('preserve_comment_position'))

        if not sql:
            return sql

        def process_segment(segment):
            if not segment:
                return segment
            if reflow:
                def repl(match):
                    content = match.group(1)
                    if freeze and 'sqlparse: off' in content.lower():
                        return match.group(0)
                    content = ' '.join(content.split())
                    return '/* {0} */'.format(content)
                segment = re.sub(r'/\*(.*?)\*/', repl, segment, flags=re.S)
            if not preserve and not keep_trailing:
                def move(m):
                    code = m.group(1).rstrip()
                    comment = m.group(2).rstrip()
                    if code:
                        return code + '\n' + comment
                    return m.group(0)
                segment = re.sub(r'([^\n]*?)(--[^\n]*)', move, segment)
            return segment

        if freeze:
            lines = sql.splitlines(True)
            result = []
            frozen = False
            buffer = ''
            for line in lines:
                stripped = line.strip().lower()
                if stripped == '-- sqlparse: off':
                    result.append(process_segment(buffer))
                    buffer = ''
                    frozen = True
                    result.append(line)
                    continue
                if stripped == '-- sqlparse: on':
                    frozen = False
                    result.append(line)
                    continue
                if frozen:
                    result.append(line)
                else:
                    buffer += line
            if buffer:
                result.append(process_segment(buffer))
            sql = ''.join(result)
        else:
            sql = process_segment(sql)
        return sql


plugins.register_plugin('comments', CommentFormatter)
