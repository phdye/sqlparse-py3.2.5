import sqlparse


def test_compact_bool_not():
    sql = 'select not (a) from foo'
    formatted = sqlparse.format(sql, spacing={'compact_bool_not': True}, keyword_case='upper')
    assert formatted == 'SELECT NOT(a) FROM foo'


def test_reserved_only_keyword_case():
    sql = 'select * from table t'
    formatted = sqlparse.format(sql, keyword_case='upper', keywords={'reserved_only': True})
    assert formatted == 'SELECT * FROM table t'


def test_identifier_quote_and_case():
    sql = 'select "MixCase" from foo'
    formatted = sqlparse.format(
        sql,
        identifier_case='lower',
        identifiers={'quote_style': 'backtick', 'keep_quoted_case': False},
    )
    assert formatted == 'select `mixcase` from foo'
