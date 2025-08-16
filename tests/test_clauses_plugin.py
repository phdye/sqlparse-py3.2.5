from sqlparse import plugins


def test_clause_breaks():
    cls = plugins.get_plugin('clauses')
    plugin = cls()
    sql = 'SELECT a FROM t WHERE b=1'
    opts = {'clauses': {'break': {'from': True, 'where': True}}}
    formatted = plugin.format(sql, opts)
    assert formatted == 'SELECT a\nFROM t\nWHERE b=1'


def test_blank_lines_before_with():
    cls = plugins.get_plugin('clauses')
    plugin = cls()
    sql = 'SELECT 1;\nWITH cte AS (SELECT 1) SELECT * FROM t'
    opts = {'clauses': {'blank_lines': {'before_with': 1}}}
    formatted = plugin.format(sql, opts)
    assert formatted == 'SELECT 1;\n\nWITH cte AS (SELECT 1) SELECT * FROM t'
