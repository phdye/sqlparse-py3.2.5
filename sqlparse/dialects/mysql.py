from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with(keywords.KEYWORDS_MYSQL)


Lexer.register_dialect(
    'mysql', initialize, aliases=('mariadb', 'mariadb-sql')
)

