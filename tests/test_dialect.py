import sqlparse
from sqlparse import lexer, tokens as T


def test_ansi_vs_postgres_keyword():
    sql = 'PERFORM 1'
    tokens_ansi = list(lexer.tokenize(sql, dialect='ansi'))
    assert tokens_ansi[0][0] is T.Name
    tokens_pg = list(lexer.tokenize(sql, dialect='postgres'))
    assert tokens_pg[0][0] is T.Keyword
