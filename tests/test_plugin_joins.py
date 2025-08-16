import warnings

import sqlparse

from sqlparse import plugins


def run_plugin(sql, opts):
    cls = plugins.get_plugin('joins')
    formatted = sqlparse.format(sql, reindent=True)
    stmt = sqlparse.parse(formatted)[0]
    stmt = cls().format(stmt, {'joins': opts})
    return str(stmt)


def test_join_alignment():
    sql = 'select * from a join b on a.id = b.id'
    formatted = run_plugin(sql, {
        'join_on_new_line': True,
        'align_on_under_join': True,
    })
    assert formatted == '\n'.join([
        'select *',
        'from a',
        'join b',
        'on a.id = b.id',
    ])


def test_join_same_line():
    sql = 'select * from a join b on a.id = b.id'
    formatted = run_plugin(sql, {
        'join_on_new_line': False,
    })
    assert formatted == '\n'.join([
        'select *',
        'from a',
        'join b on a.id = b.id',
    ])


def test_prefer_explicit_warns():
    sql = 'select * from a, b'
    cls = plugins.get_plugin('joins')
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        stmt = sqlparse.parse(sql)[0]
        cls().format(stmt, {'joins': {'prefer_explicit': True}})
        assert w
