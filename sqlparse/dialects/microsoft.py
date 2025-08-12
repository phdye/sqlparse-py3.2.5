from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with(keywords.KEYWORDS_MSACCESS)


Lexer.register_dialect(
    'microsoft', initialize, aliases=('t-sql', 'transact-sql', 'tsql')
)

