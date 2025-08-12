import re

import sqlparse
from sqlparse import keywords
from sqlparse import plugins
from sqlparse import tokens as T


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
            stmts = sqlparse.parse(text)
            parts = []
            for stmt in stmts:
                flat = list(stmt.flatten())
                for idx, tok in enumerate(flat):
                    if tok.ttype in T.Keyword and tok.value.upper() in self.RESERVED:
                        prev = None
                        j = idx - 1
                        while j >= 0:
                            pt = flat[j]
                            if not pt.is_whitespace:
                                prev = pt
                                break
                            j -= 1
                        nxt = None
                        j = idx + 1
                        length = len(flat)
                        while j < length:
                            nt = flat[j]
                            if not nt.is_whitespace:
                                nxt = nt
                                break
                            j += 1
                        if prev and prev.match(T.Keyword, 'FROM') and nxt and nxt.ttype in T.Name:
                            parts.append(tok.value)
                        else:
                            parts.append(getattr(str, case)(tok.value))
                    else:
                        parts.append(tok.value)
            text = ''.join(parts)

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
