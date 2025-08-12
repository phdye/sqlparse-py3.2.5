import sqlparse


def test_subquery_newline_and_indent():
    sql = 'SELECT * FROM (SELECT 1) x'
    formatted = sqlparse.format(
        sql,
        reindent=True,
        subqueries={
            'open_paren_same_line': False,
            'body_indent': 2,
            'close_paren_align_with_open': True,
            'prefer_keyword_on_newline': True,
        },
    )
    assert formatted == 'SELECT *\nFROM\n  (\n    SELECT 1\n  ) x'


def test_subquery_close_paren_indent():
    sql = 'SELECT * FROM (SELECT 1) x'
    formatted = sqlparse.format(
        sql,
        reindent=True,
        subqueries={
            'open_paren_same_line': True,
            'body_indent': 2,
            'close_paren_align_with_open': False,
            'prefer_keyword_on_newline': True,
        },
    )
    assert formatted == 'SELECT *\nFROM (\n    SELECT 1\n    ) x'


def test_subquery_body_indent_plus_one():
    sql = 'SELECT * FROM (SELECT 1) x'
    formatted = sqlparse.format(
        sql,
        reindent=True,
        indent_width=2,
        continuation_indent=2,
        subqueries={
            'open_paren_same_line': True,
            'body_indent': 'plus_one',
            'close_paren_align_with_open': False,
            'prefer_keyword_on_newline': True,
        },
    )
    assert formatted == 'SELECT *\nFROM (\n      SELECT 1\n      ) x'

