import sqlparse

from sqlparse.plugins.declare_cursor import DeclareCursorPlugin


def _run(sql, opts):
    stmt = sqlparse.parse(sql)[0]
    plugin = DeclareCursorPlugin()
    stmt = plugin.format(stmt, {'declare_cursor': opts, 'indent_width': 2})
    return str(stmt)


def test_declare_cursor_default_plugin():
    sql = 'EXEC SQL AT :server_alias DECLARE csr CURSOR FOR SELECT foo'
    expected = ('EXEC SQL AT :server_alias DECLARE csr CURSOR FOR\n'
                '  SELECT foo')
    assert _run(sql, {}) == expected


def test_declare_cursor_break_before_plugin():
    sql = 'EXEC SQL AT :server_alias DECLARE csr CURSOR FOR SELECT foo'
    expected = ('EXEC SQL AT :server_alias\n'
                '  DECLARE csr CURSOR FOR\n'
                '    SELECT foo')
    assert _run(sql, {'break_before': True}) == expected

