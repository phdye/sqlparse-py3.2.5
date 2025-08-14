import sqlparse


def test_pad_after_keyword_in_subquery():
    sql = ("SELECT count(*)\n"
           "FROM table1\n"
           "WHERE id = (\n"
           "    SELECT uidproduct\n"
           "    FROM table2\n"
           ")\n")
    formatted = sqlparse.format(
        sql,
        reindent_aligned=True,
        pad_after_keyword=2,
        initial_pad_after_keyword=2,
    )
    assert formatted == (
        "SELECT  count(*)\n"
        "  FROM  table1\n"
        " WHERE  id = (\n"
        "        SELECT  uidproduct\n"
        "          FROM  table2\n"
        "       )"
    )

