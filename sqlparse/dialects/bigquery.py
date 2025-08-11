from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with(keywords.KEYWORDS_BIGQUERY)


Lexer.register_dialect(
    'bigquery', initialize, aliases=('google', 'bigquery-sql')
)

