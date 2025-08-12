import sqlparse


def test_align_longest_keyword():
    sql = ("SELECT first_name, last_name\n"
           "INTO :firstName, :lastName\n"
           "FROM employees\n"
           "WHERE employee_id = :id;")
    formatted = sqlparse.format(
        sql,
        reindent_aligned=True,
        align_longest_keyword=True,
        pad_after_keyword=2,
        id_layout='single_line')
    assert formatted == ("SELECT  first_name, last_name\n"
                         "  INTO  :firstName, :lastName\n"
                         "  FROM  employees\n"
                         " WHERE  employee_id = :id;")
