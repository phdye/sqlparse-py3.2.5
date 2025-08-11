from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with()


Lexer.register_dialect('sqlite', initialize, aliases=('sqlite-sql',))

