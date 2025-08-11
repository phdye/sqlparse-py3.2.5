from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with(keywords.KEYWORDS_PLPGSQL)


Lexer.register_dialect(
    'postgres', initialize,
    aliases=('postgres-sql', 'postgresql', 'postgresql-sql')
)

