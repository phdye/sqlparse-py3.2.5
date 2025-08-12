import sqlparse.plugins as plugins


def test_cte_plugin_registration_and_formatting():
    plugin_cls = plugins.get_plugin('cte')
    assert plugin_cls is not None
    formatter = plugin_cls()
    sql = "WITH a AS (SELECT 1), b AS (SELECT 2) SELECT * FROM a"
    options = {
        'cte': {
            'one_per_line': True,
            'blank_line_between': True,
            'trailing_comma_style': 'always',
        },
        'indent_width': 2,
    }
    formatted = formatter.format(sql, options)
    expected = (
        "WITH\n"
        "  a AS (SELECT 1),\n\n"
        "  b AS (SELECT 2),\n"
        "SELECT * FROM a"
    )
    assert formatted == expected


def test_cte_plugin_no_options_returns_input():
    plugin_cls = plugins.get_plugin('cte')
    formatter = plugin_cls()
    sql = "WITH a AS (SELECT 1) SELECT * FROM a"
    assert formatter.format(sql, {}) == sql
