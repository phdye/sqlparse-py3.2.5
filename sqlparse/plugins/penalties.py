"""Penalty tuning plugin.

This plugin applies simple line-breaking rules based on penalty options
provided via ``options['penalties']``.  It demonstrates how configuration
values can influence formatting without touching the core formatter.

The implementation is intentionally small and compatible with Python 3.2.5.
"""

import sqlparse
from sqlparse import plugins
from sqlparse import sql, tokens as T


class PenaltyTuning(object):
    """Apply line breaks based on penalty options.

    The algorithm is deliberately straightforward: if a penalty option is
    set to ``0`` the corresponding line break is inserted.  Any positive
    value leaves the original layout untouched.  This simplistic cost model
    allows tests to toggle behaviours without implementing a full wrapping
    engine.
    """

    def format(self, stream, options):
        penalties = options.get('penalties') or {}
        if isinstance(stream, str):
            statements = sqlparse.parse(stream)
        else:
            statements = list(stream)
        for stmt in statements:
            self._apply_select_breaks(stmt, penalties)
            self._apply_from_where_breaks(stmt, penalties)
            self._apply_boolean_breaks(stmt, penalties)
        return ''.join([str(s) for s in statements])

    def _apply_select_breaks(self, stmt, penalties):
        idx, token = stmt.token_next_by(m=(T.Keyword.DML, 'SELECT'))
        if token is None:
            return
        if penalties.get('break_after_select', 1) <= 0:
            stmt.insert_after(idx, sql.Token(T.Whitespace, '\n'))
        if penalties.get('break_before_first_select_item', 1) <= 0:
            tidx, first = stmt.token_next(idx, skip_ws=True)
            if first is not None:
                stmt.insert_before(tidx, sql.Token(T.Whitespace, '\n'))
        if penalties.get('keep_short_select_items_together', 1) <= 0:
            cidx = idx
            while True:
                cidx, comma = stmt.token_next_by(m=(T.Punctuation, ','), idx=cidx)
                if comma is None:
                    break
                stmt.insert_after(cidx, sql.Token(T.Whitespace, '\n'))

    def _apply_from_where_breaks(self, stmt, penalties):
        if penalties.get('break_before_from', 1) <= 0:
            idx, token = stmt.token_next_by(m=(T.Keyword, 'FROM'))
            if token is not None:
                stmt.insert_before(idx, sql.Token(T.Whitespace, '\n'))
        if penalties.get('break_before_where', 1) <= 0:
            idx, token = stmt.token_next_by(i=sql.Where)
            if token is not None:
                stmt.insert_before(idx, sql.Token(T.Whitespace, '\n'))

    def _apply_boolean_breaks(self, stmt, penalties):
        if penalties.get('break_in_boolean_chain', 1) <= 0:
            _, where = stmt.token_next_by(i=sql.Where)
            if where is None:
                return
            idx = -1
            while True:
                idx, token = where.token_next_by(m=(T.Keyword, ('AND', 'OR')), idx=idx)
                if token is None:
                    break
                where.insert_before(idx, sql.Token(T.Whitespace, '\n'))
                idx += 1
        

plugins.register_plugin('penalties', PenaltyTuning)
