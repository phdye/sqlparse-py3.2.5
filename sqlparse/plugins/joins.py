import warnings

from sqlparse import plugins, sql, tokens as T


class JoinPlugin(object):
    """Formatter plugin implementing join configuration options."""

    def format(self, stream, options):
        """Format *stream* according to join options.

        If *stream* is a :class:`Statement` the token tree is modified in-place
        according to ``joins`` options. For other stream types the input is
        returned unchanged.
        """
        if stream is None:
            return stream
        join_opts = options.get('joins') or {}
        if hasattr(stream, 'token_next'):
            return self._postprocess(stream, join_opts)
        return stream

    def _postprocess(self, stmt, join_opts):
        join_on_new_line = bool(join_opts.get('join_on_new_line'))
        align_on_under_join = bool(join_opts.get('align_on_under_join'))
        prefer_explicit = bool(join_opts.get('prefer_explicit'))

        if prefer_explicit:
            self._check_comma_join(stmt)

        if not join_on_new_line and not align_on_under_join:
            return stmt

        tokens = list(stmt.flatten())
        length = len(tokens)
        i = 0
        while i < length:
            tok = tokens[i]
            if tok.is_keyword and 'JOIN' in tok.normalized:
                j = i + 1
                while j < length:
                    nt = tokens[j]
                    if nt.is_keyword and nt.normalized == 'ON':
                        self._adjust_on(tokens, i, j, join_on_new_line,
                                         align_on_under_join)
                        break
                    if nt.is_keyword and 'JOIN' in nt.normalized:
                        break
                    if nt.is_keyword and nt.normalized in (
                            'WHERE', 'GROUP', 'ORDER', 'LIMIT'):
                        break
                    j += 1
                i = j
            i += 1
        return stmt

    def _adjust_on(self, tokens, join_idx, on_idx, new_line, align):
        on_tok = tokens[on_idx]

        join_indent = 0
        if join_idx > 0:
            prev = tokens[join_idx - 1]
            if prev.is_whitespace:
                parts = prev.value.split('\n')
                join_indent = len(parts[-1])

        if new_line:
            indent = join_indent
            if not align:
                indent += 2
            prev = tokens[on_idx - 1]
            ws = '\n' + ' ' * indent
            if prev.is_whitespace:
                prev.value = ws
            else:
                on_tok.parent.insert_before(on_tok, sql.Token(T.Whitespace, ws))
        else:
            prev = tokens[on_idx - 1]
            if prev.is_whitespace:
                prev.value = ' '
            else:
                on_tok.parent.insert_before(on_tok, sql.Token(T.Whitespace, ' '))

    def _check_comma_join(self, stmt):
        tokens = list(stmt.flatten())
        in_from = False
        for tok in tokens:
            if tok.is_keyword and tok.normalized == 'FROM':
                in_from = True
                continue
            if in_from:
                if tok.ttype in T.Punctuation and tok.value == ',':
                    warnings.warn('comma join detected', UserWarning)
                    return
                if tok.is_keyword and tok.normalized in (
                        'WHERE', 'GROUP', 'ORDER', 'LIMIT'):
                    return


plugins.register_plugin('joins', JoinPlugin)

