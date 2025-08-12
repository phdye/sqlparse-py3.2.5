import sqlparse


def test_into_comma_first():
    sql = ("EXEC SQL\n"
           "SELECT first_name, last_name\n"
           "INTO :firstName, :lastName\n"
           "FROM employees\n"
           "WHERE employee_id = :id;")
    formatted = sqlparse.format(
        sql,
        keyword_case='upper',
        strip_whitespace=True,
        reindent_aligned=True,
        pad_after_keyword=2,
        align_longest_keyword=True,
        comma_first=True,
        initial_indent=4,
        initial_pad_after_keyword=2,
        id_layout='hanging')
    expected = open('behavior/down/into.expected.sql').read().strip()
    assert formatted.strip() == expected
