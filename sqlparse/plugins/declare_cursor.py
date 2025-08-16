from sqlparse import plugins, sql, tokens as T


class DeclareCursorPlugin(object):
    """Formatter plugin implementing DECLARE CURSOR configuration options."""

    def format(self, stream, options):
        if stream is None:
            return stream

        opts = options.get('declare_cursor') or {}
        break_before = bool(opts.get('break_before'))

        if hasattr(stream, 'token_next'):
            return self._postprocess(stream, options, break_before)

        # Only manipulate statements during postprocess. For other phases
        # (token generator or final string) return input unchanged.
        return stream

    def _postprocess(self, stmt, options, break_before):
        indent_width = options.get('indent_width', 2)

        didx, declare_tok = stmt.token_next_by(m=(T.Keyword, 'DECLARE'))
        if declare_tok is None:
            return stmt

        fidx, for_tok = stmt.token_next_by(m=(T.Keyword, 'FOR'), idx=didx)
        if for_tok is None:
            return stmt

        if break_before:
            pidx, prev_tok = stmt.token_prev(didx, skip_ws=False)
            ws = '\n' + ' ' * indent_width
            if prev_tok is not None and prev_tok.is_whitespace:
                prev_tok.value = ws
            else:
                stmt.insert_before(declare_tok, sql.Token(T.Whitespace, ws))
                fidx += 1
                didx += 1

        base = indent_width * (1 if break_before else 0)
        ws_query = '\n' + ' ' * (base + indent_width)
        nidx, next_tok = stmt.token_next(fidx, skip_ws=False)
        if next_tok is not None and next_tok.is_whitespace:
            next_tok.value = ws_query
        else:
            stmt.insert_after(for_tok, sql.Token(T.Whitespace, ws_query))

        return stmt


plugins.register_plugin('declare_cursor', DeclareCursorPlugin)

