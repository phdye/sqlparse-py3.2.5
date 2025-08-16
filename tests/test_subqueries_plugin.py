import sqlparse


def _run_plugin(sql, opts, **fmt_opts):
    formatted = sqlparse.format(sql, **fmt_opts)
    stmt = sqlparse.parse(formatted)[0]
    from sqlparse.plugins import get_plugin
    cls = get_plugin('subqueries')
    stmt = cls().format(stmt, {'subqueries': opts, 'indent_width': fmt_opts.get('indent_width', 2)})
    return str(stmt)


def test_subquery_newline_and_indent():
    sql = 'SELECT * FROM (SELECT 1) x'
    formatted = _run_plugin(
        sql,
        {
            'open_paren_same_line': False,
            'body_indent': 2,
            'close_paren_align_with_open': True,
            'prefer_keyword_on_newline': True,
        },
        reindent=True,
    )
    assert formatted == 'SELECT *\nFROM\n  (\n    SELECT 1\n  ) x'


def test_subquery_close_paren_indent():
    sql = 'SELECT * FROM (SELECT 1) x'
    formatted = _run_plugin(
        sql,
        {
            'open_paren_same_line': True,
            'body_indent': 2,
            'close_paren_align_with_open': False,
            'prefer_keyword_on_newline': True,
        },
        reindent=True,
    )
    assert formatted == 'SELECT *\nFROM (\n  SELECT 1\n  ) x'


def test_subquery_body_indent_plus_one():
    sql = 'SELECT * FROM (SELECT 1) x'
    formatted = _run_plugin(
        sql,
        {
            'open_paren_same_line': True,
            'body_indent': 'plus_one',
            'close_paren_align_with_open': True,
            'prefer_keyword_on_newline': True,
        },
        reindent=True,
        indent_width=4,
    )
    assert formatted == 'SELECT *\nFROM (\n    SELECT 1\n) x'

