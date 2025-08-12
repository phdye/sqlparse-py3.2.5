import sqlparse


def test_strict_keywords():
    sql = 'select fetch from dual'
    res = sqlparse.format(sql, keyword_case='upper', dialect='oracle')
    assert res == 'SELECT FETCH FROM dual'
    res = sqlparse.format(
        sql,
        keyword_case='upper',
        dialect='oracle',
        dialect_options={'strict_keywords': True})
    assert res == 'SELECT fetch FROM dual'


def test_continuation_indent():
    sql = 'select foo, bar, baz from dual'
    res = sqlparse.format(
        sql,
        reindent=True,
        wrap_after=14,
        layout={'continuation_indent': 4})
    assert res == 'select foo, bar,\n    baz\nfrom dual'
