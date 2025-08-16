import sqlparse
from sqlparse import plugins


def get_plugin():
    cls = plugins.get_plugin('create_table')
    return cls()


def test_create_table_one_column_per_line():
    plugin = get_plugin()
    sql = 'CREATE TABLE foo(id INT, name TEXT);'
    opts = {'create_table': {'one_column_per_line': True}}
    result = plugin.format(sql, opts)
    expected = 'CREATE TABLE foo (\n  id INT,\n  name TEXT\n);'
    assert result == expected


def test_create_table_comma_first():
    plugin = get_plugin()
    sql = 'CREATE TABLE foo(id INT, name TEXT);'
    opts = {'create_table': {'one_column_per_line': True, 'comma_last': False}}
    result = plugin.format(sql, opts)
    expected = 'CREATE TABLE foo (\n  id INT\n  , name TEXT\n);'
    assert result == expected


def test_create_table_align_columns():
    plugin = get_plugin()
    sql = 'CREATE TABLE foo(id INT, name TEXT);'
    opts = {'create_table': {'one_column_per_line': True, 'align_columns': True}}
    result = plugin.format(sql, opts)
    expected = 'CREATE TABLE foo (\n  id   INT,\n  name TEXT\n);'
    assert result == expected
