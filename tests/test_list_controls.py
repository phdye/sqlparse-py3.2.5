import sqlparse


def test_lists_break_after_comma():
    sql = 'SELECT a, b, c'
    res = sqlparse.format(sql, lists={'break_after_comma': True})
    assert res == 'SELECT a,\nb,\nc'


def test_lists_bin_pack():
    sql = 'SELECT a,\n b,\n c'
    res = sqlparse.format(sql, lists={'bin_pack': True})
    assert res == 'SELECT a, b, c'


def test_lists_align_after_open_paren():
    sql = 'SELECT func(\n a,\n b\n)'
    res = sqlparse.format(sql, lists={'align_after_open_paren': True})
    assert res == 'SELECT func(\n     a,\n b\n)'


def test_lists_leading_commas_wrap_after():
    sql = 'SELECT a, b, c'
    res = sqlparse.format(sql, reindent=True, lists={'leading_commas': True, 'wrap_after': 1})
    assert res == 'SELECT a\n     , b\n     , c'


def test_lists_trailing_comma_in_select():
    sql = 'SELECT a, b, FROM t'
    res = sqlparse.format(sql, lists={'trailing_comma_in_select': False})
    assert res == 'SELECT a, b FROM t'
    sql2 = 'SELECT a, b FROM t'
    res2 = sqlparse.format(sql2, lists={'trailing_comma_in_select': True})
    assert res2 == 'SELECT a, b, FROM t'
