import re

from sqlparse import keywords
from sqlparse import plugins


class SpacingCasing(object):
    """Formatter plugin providing spacing and casing options."""

    RESERVED = set(k.upper() for k in keywords.KEYWORDS_COMMON.keys())

    def format(self, text, options):
        spacing = options.get('spacing') or {}
        if spacing.get('compact_bool_not'):
            text = re.sub(r'\bNOT\s+\(', 'NOT(', text, flags=re.IGNORECASE)

        kw_opts = options.get('keywords') or {}
        case = options.get('keyword_case')
        if case and kw_opts.get('reserved_only'):
            pattern = r'\b(' + '|'.join(self.RESERVED) + r')\b'
            def repl(match):
                word = match.group(0)
                return getattr(str, case)(word)
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        ident_opts = options.get('identifiers') or {}
        quote_style = ident_opts.get('quote_style')
        keep_case = ident_opts.get('keep_quoted_case', True)
        id_case = options.get('identifier_case')

        if quote_style == 'backtick':
            left = right = '`'
        elif quote_style == 'bracket':
            left, right = '[', ']'
        else:
            left = right = '"'

        if quote_style:
            def repl_quotes(match):
                inner = match.group(1) or match.group(2) or match.group(3)
                if not keep_case and id_case:
                    inner = getattr(str, id_case)(inner)
                return left + inner + right
            text = re.sub(r'"([^"]*)"|`([^`]*)`|\[([^\]]*)\]', repl_quotes, text)
        elif id_case and not keep_case:
            def repl_case(match):
                inner = getattr(str, id_case)(match.group(1))
                return '"' + inner + '"'
            text = re.sub(r'"([^"]*)"', repl_case, text)

        return text


plugins.register_plugin('spacing_casing', SpacingCasing)
