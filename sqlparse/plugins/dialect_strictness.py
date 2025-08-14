import sys
from sqlparse import plugins, keywords, tokens as T

@plugins.register_plugin('dialect_strictness')
class DialectStrictness(object):
    """Handle dialect.strict_keywords and layout.continuation_indent."""

    def format(self, stream, options):
        print(": sqlparse.plugins.dialect_strictness.format(...)", file=sys.stderr)
        if hasattr(stream, 'token_next'):
            return self._postprocess(stream, options)
        return self._preprocess(stream, options)

    def _preprocess(self, stream, options):
        strict = False
        dialect_opts = options.get('dialect_options') or {}
        if 'strict_keywords' in dialect_opts:
            strict = dialect_opts['strict_keywords']
        if not strict:
            for item in stream:
                yield item
            return
        dialect = options.get('dialect')
        allowed = {}
        allowed.update(keywords.KEYWORDS_COMMON)
        if dialect:
            name = 'KEYWORDS_{0}'.format(str(dialect).upper())
            kw = getattr(keywords, name, {})
            allowed.update(kw)
        else:
            allowed.update(keywords.KEYWORDS)
        allowed_keys = set(allowed.keys())
        for ttype, value in stream:
            if ttype in T.Keyword and value.upper() not in allowed_keys:
                yield T.Name, value
            else:
                yield ttype, value

    def _postprocess(self, stmt, options):
        layout = options.get('layout') or {}
        cont = layout.get('continuation_indent')
        if not cont:
            return stmt
        try:
            cont = int(cont)
        except Exception:
            return stmt
        indent_width = options.get('indent_width', 2)
        tokens = list(stmt.flatten())
        level = 0
        i = 0
        length = len(tokens)
        while i < length:
            tok = tokens[i]
            if tok.match(T.Punctuation, '('):
                level += 1
            elif tok.match(T.Punctuation, ')'):
                if level:
                    level -= 1
            elif tok.is_whitespace and '\n' in tok.value:
                j = i + 1
                next_tok = None
                while j < length:
                    nt = tokens[j]
                    if not nt.is_whitespace:
                        next_tok = nt
                        break
                    j += 1
                if next_tok is None:
                    i += 1
                    continue
                if next_tok.ttype in T.Keyword:
                    indent = indent_width * level
                else:
                    indent = indent_width * level + cont
                tok.value = '\n' + ' ' * indent
            i += 1
        return stmt
