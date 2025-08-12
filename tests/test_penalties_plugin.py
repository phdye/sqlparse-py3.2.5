import sqlparse

import sqlparse
from sqlparse import plugins
import sqlparse.plugins.penalties  # noqa: F401


def _run_plugin(sql, penalties):
    statements = list(sqlparse.parse(sql))
    plugin_cls = plugins.get_plugin('penalties')
    plugin = plugin_cls()
    formatted = plugin.format(statements, {'penalties': penalties})
    return ''.join(str(s) for s in formatted)


def test_penalties_insert_breaks():
    sql = 'SELECT a, b FROM foo WHERE x AND y'
    formatted = _run_plugin(sql, {
        'break_after_select': 0,
        'break_before_first_select_item': 0,
        'keep_short_select_items_together': 0,
        'break_before_from': 0,
        'break_before_where': 0,
        'break_in_boolean_chain': 0,
    })
    assert 'SELECT \n' in formatted
    assert '\nFROM' in formatted
    assert '\nWHERE' in formatted
    assert '\nAND' in formatted


def test_penalties_no_changes_when_positive():
    sql = 'SELECT a, b FROM foo WHERE x AND y'
    formatted = _run_plugin(sql, {
        'break_after_select': 100,
        'break_before_first_select_item': 100,
        'keep_short_select_items_together': 100,
        'break_before_from': 100,
        'break_before_where': 100,
        'break_in_boolean_chain': 100,
    })
    assert formatted == sql
