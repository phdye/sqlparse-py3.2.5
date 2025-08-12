#
# Copyright (C) 2009-2020 the sqlparse authors and contributors
# <see AUTHORS file>
#
# This module is part of python-sqlparse and is released under
# the BSD License: https://opensource.org/licenses/BSD-3-Clause

from sqlparse import sql, tokens as T
from sqlparse.utils import offset, indent


class AlignedIndentFilter:
    join_words = (r'((LEFT\s+|RIGHT\s+|FULL\s+)?'
                  r'(INNER\s+|OUTER\s+|STRAIGHT\s+)?|'
                  r'(CROSS\s+|NATURAL\s+)?)?JOIN\b')
    by_words = r'(GROUP|ORDER)\s+BY\b'
    split_words = ('FROM',
                   join_words, 'ON', by_words,
                   'INTO', 'WHERE', 'AND', 'OR',
                   'HAVING', 'LIMIT',
                   'UNION', 'VALUES',
                   'SET', 'BETWEEN', 'EXCEPT')

    def __init__(self, char=' ', n='\n', pad_after_keyword=1,
                 align_longest_keyword=False, id_layout='vertical',
                 initial_indent=0, initial_pad_after_keyword=None):
        self.n = n
        self.offset = initial_indent
        self.indent = 0
        self.char = char
        self.pad_after_keyword = pad_after_keyword
        self.initial_pad_after_keyword = initial_pad_after_keyword
        self.align_longest_keyword = align_longest_keyword
        self.id_layout = id_layout
        self._max_kwd_len = len('select')

    def nl(self, offset=1):
        # offset = 1 represent a single space after SELECT
        offset = -len(offset) if not isinstance(offset, int) else offset
        # add two for the space and parenthesis
        indent = self.indent * (2 + self._max_kwd_len)

        return sql.Token(T.Whitespace, self.n + self.char * (
            self._max_kwd_len + offset + indent + self.offset))

    def _process_statement(self, tlist):
        if len(tlist.tokens) > 0 and tlist.tokens[0].is_whitespace \
                and self.indent == 0:
            tlist.tokens.pop(0)

        if self.offset > 0 or self.initial_pad_after_keyword is not None:
            idx, token = tlist.token_next_by(t=(T.DML,))
            if token is not None and idx > 0:
                pidx, prev_ = tlist.token_prev(idx)
                nl = self.nl(str(token))
                if prev_ is not None and prev_.ttype in T.Whitespace:
                    prev_.value = nl.value
                else:
                    tlist.insert_before(token, nl)
            if token is not None:
                self._pad_after_keyword(tlist, token, initial=True)
        elif tlist.tokens and tlist.tokens[0].ttype in T.Keyword:
            self._pad_after_keyword(tlist, tlist.tokens[0])

        # process the main query body
        self._process(sql.TokenList(tlist.tokens))

    def _process_parenthesis(self, tlist):
        # if this isn't a subquery, don't re-indent
        _, token = tlist.token_next_by(m=(T.DML, 'SELECT'))
        if token is not None:
            with indent(self):
                tlist.insert_after(tlist[0], self.nl('SELECT'))
                # process the inside of the parenthesis
                self._process_default(tlist)

            # de-indent last parenthesis
            tlist.insert_before(tlist[-1], self.nl())

    def _process_identifierlist(self, tlist):
        # columns being selected
        if self.id_layout != 'single_line':
            identifiers = list(tlist.get_identifiers())
            identifiers.pop(0)
            [tlist.insert_before(token, self.nl()) for token in identifiers]
        self._process_default(tlist)

    def _process_case(self, tlist):
        offset_ = len('case ') + len('when ')
        cases = tlist.get_cases(skip_ws=True)
        # align the end as well
        end_token = tlist.token_next_by(m=(T.Keyword, 'END'))[1]
        cases.append((None, [end_token]))

        condition_width = [len(' '.join(map(str, cond))) if cond else 0
                           for cond, _ in cases]
        max_cond_width = max(condition_width)

        for i, (cond, value) in enumerate(cases):
            # cond is None when 'else or end'
            stmt = cond[0] if cond else value[0]

            if i > 0:
                tlist.insert_before(stmt, self.nl(offset_ - len(str(stmt))))
            if cond:
                ws = sql.Token(T.Whitespace, self.char * (
                    max_cond_width - condition_width[i]))
                tlist.insert_after(cond[-1], ws)

    def _next_token(self, tlist, idx=-1):
        split_words = T.Keyword, self.split_words, True
        tidx, token = tlist.token_next_by(m=split_words, idx=idx)
        # treat "BETWEEN x and y" as a single statement
        if token and token.normalized == 'BETWEEN':
            tidx, token = self._next_token(tlist, tidx)
            if token and token.normalized == 'AND':
                tidx, token = self._next_token(tlist, tidx)
        return tidx, token

    def _pad_after_keyword(self, tlist, token, initial=False):
        pad_len = self.pad_after_keyword
        if initial and self.initial_pad_after_keyword is not None:
            pad_len = self.initial_pad_after_keyword
        if pad_len is None:
            return
        pad = self.char * pad_len
        idx = tlist.token_index(token)
        nidx, next_ = tlist.token_next(idx, skip_ws=False)
        if next_ is None:
            tlist.insert_after(token, sql.Token(T.Whitespace, pad))
        elif next_.is_whitespace:
            next_.value = pad
        else:
            tlist.insert_after(token, sql.Token(T.Whitespace, pad))

    def _split_kwds(self, tlist):
        if self.align_longest_keyword:
            tokens = []
            tidx, token = self._next_token(tlist)
            while token:
                if (
                    token.match(T.Keyword, self.join_words, regex=True)
                    or token.match(T.Keyword, self.by_words, regex=True)
                ):
                    token_indent = token.value.split()[0]
                else:
                    token_indent = str(token)
                self._max_kwd_len = max(self._max_kwd_len,
                                        len(token_indent))
                tokens.append((token, token_indent))
                tidx, token = self._next_token(tlist, tidx)
            for token, token_indent in tokens:
                tlist.insert_before(token, self.nl(token_indent))
                self._pad_after_keyword(tlist, token)
        else:
            tidx, token = self._next_token(tlist)
            while token:
                if (
                    token.match(T.Keyword, self.join_words, regex=True)
                    or token.match(T.Keyword, self.by_words, regex=True)
                ):
                    token_indent = token.value.split()[0]
                else:
                    token_indent = str(token)
                tlist.insert_before(token, self.nl(token_indent))
                self._pad_after_keyword(tlist, token)
                tidx += 1
                tidx, token = self._next_token(tlist, tidx)

    def _process_default(self, tlist):
        self._split_kwds(tlist)
        # process any sub-sub statements
        for sgroup in tlist.get_sublists():
            idx = tlist.token_index(sgroup)
            pidx, prev_ = tlist.token_prev(idx)
            # HACK: make "group/order by" work. Longer than max_len.
            offset_ = 3 if (
                prev_ and prev_.match(T.Keyword, self.by_words, regex=True)
            ) else 0
            with offset(self, offset_):
                self._process(sgroup)

    def _process(self, tlist):
        func_name = '_process_{cls}'.format(cls=type(tlist).__name__)
        func = getattr(self, func_name.lower(), self._process_default)
        func(tlist)

    def process(self, stmt):
        self._process(stmt)
        return stmt
