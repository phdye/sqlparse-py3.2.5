from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex._init_with(keywords.KEYWORDS_SNOWFLAKE)


Lexer.register_dialect('snowflake', initialize, aliases=('snowflake-sql',))

