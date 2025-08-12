import sqlparse


def test_id_layout_hanging():
    sql = "select a, b, c from foo;"
    formatted = sqlparse.format(sql, reindent_aligned=True, id_layout='hanging')
    assert formatted == "select a,\n       b,\n       c\n  from foo;"

