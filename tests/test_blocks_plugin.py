from sqlparse import plugins
import sqlparse.plugins.blocks  # noqa: F401  ensure registration


def _run(sql, options):
    cls = plugins.get_plugin('blocks')
    assert cls is not None
    return cls().format(sql, options)


def test_blocks_formatting():
    sql = (
        "IF cond THEN\n"
        "BEGIN\n"
        "  NULL;\n"
        "END;\n"
        "END IF;\n"
    )
    options = {
        'blocks': {
            'begin_same_line': True,
            'end_own_line': True,
            'align_end_with_opener': True,
        }
    }
    expected = (
        "IF cond THEN BEGIN\n"
        "  NULL;\n"
        "END;\n"
        "END IF;\n"
    )
    assert _run(sql, options) == expected


def test_declaration_alignment():
    sql = (
        "DECLARE\n"
        "  a NUMBER; b VARCHAR2(10):= 'x';\n"
        "BEGIN\n"
        "  NULL;\n"
        "END;\n"
    )
    options = {
        'blocks': {
            'end_own_line': True,
            'align_end_with_opener': True,
        },
        'declarations': {
            'one_per_line': True,
            'align_types': True,
            'align_assignment': True,
        },
    }
    expected = (
        "DECLARE\n"
        "  a NUMBER;\n"
        "  b VARCHAR2(10) := 'x';\n"
        "BEGIN\n"
        "  NULL;\n"
        "END;\n"
    )
    assert _run(sql, options) == expected


def test_label_column():
    sql = (
        "  <<lbl>>\n"
        "BEGIN\n"
        "  NULL;\n"
        "END lbl;\n"
    )
    options = {'blocks': {'label_column': 0, 'align_end_with_opener': True}}
    expected = (
        "<<lbl>>\n"
        "BEGIN\n"
        "  NULL;\n"
        "END lbl;\n"
    )
    assert _run(sql, options) == expected
