from sqlparse import keywords
from sqlparse.lexer import Lexer


def initialize(lex):
    lex.clear()
    lex.set_SQL_REGEX(keywords.SQL_REGEX)
    lex.add_keywords(keywords.KEYWORDS_COMMON)
    lex.add_keywords(keywords.KEYWORDS_ORACLE)
    lex.add_keywords(keywords.KEYWORDS_MYSQL)
    lex.add_keywords(keywords.KEYWORDS_PLPGSQL)
    lex.add_keywords(keywords.KEYWORDS_HQL)
    lex.add_keywords(keywords.KEYWORDS_MSACCESS)
    lex.add_keywords(keywords.KEYWORDS_SNOWFLAKE)
    lex.add_keywords(keywords.KEYWORDS_BIGQUERY)
    lex.add_keywords(keywords.KEYWORDS)


Lexer.register_dialect('default', initialize, aliases=('flexible',))

