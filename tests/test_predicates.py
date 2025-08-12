import sqlparse


class TestPredicateLayout:
    def test_compact(self):
        sql = 'SELECT * FROM foo WHERE a=1 AND b=2 OR c=3'
        res = sqlparse.format(sql, predicates={'layout': 'compact'})
        assert res == sql

    def test_one_per_line(self):
        sql = 'SELECT * FROM foo WHERE a=1 AND b=2 OR c=3'
        res = sqlparse.format(sql, predicates={'layout': 'one_per_line'})
        assert res == (
            'SELECT * FROM foo WHERE\n'
            '  a=1\n'
            '  AND b=2\n'
            '  OR c=3'
        )

    def test_heuristic(self):
        sql = 'SELECT * FROM foo WHERE a=1 AND b=2 OR c=3'
        res = sqlparse.format(sql, predicates={'layout': 'heuristic'})
        assert res == (
            'SELECT * FROM foo WHERE\n'
            '  a=1\n'
            '  AND b=2\n'
            '  OR c=3'
        )

    def test_heuristic_no_break(self):
        sql = 'SELECT * FROM foo WHERE a=1 AND b=2'
        res = sqlparse.format(sql, predicates={'layout': 'heuristic'})
        assert res == sql

