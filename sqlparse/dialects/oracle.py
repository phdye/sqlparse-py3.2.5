from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with(keywords.KEYWORDS_ORACLE)


Lexer.register_dialect('oracle', initialize, aliases=('plsql',))

