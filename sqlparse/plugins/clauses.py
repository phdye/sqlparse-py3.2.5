import sys
from sqlparse import plugins


class Clauses(object):
    """Formatter plugin to control clause breaks and blank lines."""

    CLAUSE_KEYS = (
        'select', 'from', 'where', 'group_by', 'having', 'order_by',
        'window', 'join', 'on', 'with', 'values'
    )

    BLANK_KEYS = (
        'before_with', 'before_create', 'before_block'
    )

    def format(self, stream, options):
        """Format *stream* according to clause options in *options*."""
        print(": sqlparse.plugins.clauses.format(...)", file=sys.stderr)
        text = stream
        if isinstance(stream, (list, tuple)):
            text = ''.join(stream)

        opts = options.get('clauses') or {}
        breaks = opts.get('break') or {}
        blanks = opts.get('blank_lines') or {}

        for key in self.CLAUSE_KEYS:
            if breaks.get(key):
                keyword = self._clause_keyword(key)
                text = self._break_before(text, keyword)

        for key in self.BLANK_KEYS:
            count = blanks.get(key)
            if count:
                keyword = self._blank_keyword(key)
                text = self._blank_before(text, keyword, count)

        return text

    def _clause_keyword(self, key):
        return key.replace('_', ' ').upper()

    def _break_before(self, text, keyword):
        return text.replace(' ' + keyword, '\n' + keyword)

    def _blank_keyword(self, key):
        if key == 'before_with':
            return 'WITH'
        if key == 'before_create':
            return 'CREATE'
        if key == 'before_block':
            return 'BEGIN'
        return key.upper()

    def _blank_before(self, text, keyword, count):
        try:
            count = int(count)
        except Exception:
            return text
        if count < 1:
            return text
        seq = '\n' * (count + 1) + keyword
        return text.replace('\n' + keyword, seq)

plugins.register_plugin('clauses', Clauses)
