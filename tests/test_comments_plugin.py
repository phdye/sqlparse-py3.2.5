from sqlparse.plugins import get_plugin


def _format(sql, **opts):
    plugin_cls = get_plugin('comments')
    plugin = plugin_cls()
    return plugin.format(sql, {'comments': opts})


def test_reflow_block_comments():
    sql = 'SELECT 1; /*  foo   bar   baz  */'
    res = _format(sql, reflow_block_comments=True)
    assert res == 'SELECT 1; /* foo bar baz */'


def test_move_trailing_line_comment():
    sql = 'SELECT 1 -- comment'
    res = _format(sql, keep_trailing_line_comment_with_code=False)
    assert res == 'SELECT 1\n-- comment'


def test_preserve_trailing_comment():
    sql = 'SELECT 1 -- comment'
    res = _format(
        sql,
        keep_trailing_line_comment_with_code=False,
        preserve_comment_position=True,
    )
    assert res == 'SELECT 1 -- comment'


def test_freeze_directives():
    sql = (
        'SELECT 1 -- keep\n'
        '-- sqlparse: off\n'
        'SELECT 2 -- frozen\n'
        '-- sqlparse: on\n'
        '/* foo   bar */'
    )
    res = _format(
        sql,
        pragma_freeze_directives=True,
        keep_trailing_line_comment_with_code=False,
        reflow_block_comments=True,
    )
    expected = (
        'SELECT 1\n'
        '-- keep\n'
        '-- sqlparse: off\n'
        'SELECT 2 -- frozen\n'
        '-- sqlparse: on\n'
        '/* foo bar */'
    )
    assert res == expected
