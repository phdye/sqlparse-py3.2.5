from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with()


Lexer.register_dialect('ansi', initialize, aliases=('ansi-sql',))

