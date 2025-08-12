import sqlparse.plugins.case_expr  # ensure registration
from sqlparse import plugins


def test_case_expr_formatting_align_then():
    formatter = plugins.get_plugin('case_expr')()
    sql = 'CASE WHEN foo=1 THEN x WHEN foo=20 THEN y ELSE z END'
    opts = {
        'case_expr': {
            'indent_when_then': True,
            'align_then': True,
            'end_align_with_case': True,
        },
        'indent_width': 2,
        'indent_char': ' '
    }
    formatted = formatter.format(sql, opts)
    expected = 'CASE\n  WHEN foo=1  THEN x\n  WHEN foo=20 THEN y\n  ELSE z\nEND'
    assert formatted == expected


def test_case_expr_end_indented():
    formatter = plugins.get_plugin('case_expr')()
    sql = 'CASE WHEN foo=1 THEN x END'
    opts = {
        'case_expr': {
            'indent_when_then': True,
            'align_then': False,
            'end_align_with_case': False,
        },
        'indent_width': 2,
        'indent_char': ' '
    }
    formatted = formatter.format(sql, opts)
    expected = 'CASE\n  WHEN foo=1 THEN x\n  END'
    assert formatted == expected
