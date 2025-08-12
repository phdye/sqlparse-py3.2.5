#
# Copyright (C) 2009-2020 the sqlparse authors and contributors
# <see AUTHORS file>
#
# This module is part of python-sqlparse and is released under
# the BSD License: https://opensource.org/licenses/BSD-3-Clause

"""Parse SQL statements."""

# Setup namespace
from sqlparse import sql
from sqlparse import cli
from sqlparse import engine
from sqlparse import tokens
from sqlparse import filters
from sqlparse import formatter
from sqlparse import config
from sqlparse import plugins


__version__ = '0.5.3'
__all__ = ['engine', 'filters', 'formatter', 'sql', 'tokens', 'cli', 'config',
           'plugins']


def parse(sql, encoding=None, dialect=None):
    """Parse sql and return a list of statements.

    :param sql: A string containing one or more SQL statements.
    :param encoding: The encoding of the statement (optional).
    :returns: A tuple of :class:`~sqlparse.sql.Statement` instances.
    """
    return tuple(parsestream(sql, encoding, dialect))


def parsestream(stream, encoding=None, dialect=None):
    """Parses sql statements from file-like object.

    :param stream: A file-like object.
    :param encoding: The encoding of the stream contents (optional).
    :returns: A generator of :class:`~sqlparse.sql.Statement` instances.
    """
    stack = engine.FilterStack(dialect=dialect)
    stack.enable_grouping()
    return stack.run(stream, encoding)


def format(sql, encoding=None, **options):
    """Format *sql* according to *options*.

    Available options are documented in :ref:`formatting`.

    In addition to the formatting options this function accepts the
    keyword "encoding" which determines the encoding of the statement.

    :returns: The formatted SQL statement as string.
    """
    dialect = options.pop('dialect', None)
    newline_at_eof = options.pop('newline_at_eof', None)
    stack = engine.FilterStack(dialect=dialect)
    options = formatter.validate_options(options)
    stack = formatter.build_filter_stack(stack, options)
    stack.postprocess.append(filters.SerializerUnicode())
    result = ''.join(stack.run(sql, encoding))

    for key in options:
        if plugins.get_plugin(key) is None:
            try:
                __import__('sqlparse.plugins.{0}'.format(key), fromlist=['_'])
            except Exception:
                continue

    for name in plugins.available_plugins():
        if name in options:
            plugin_cls = plugins.get_plugin(name)
            if plugin_cls is not None:
                plugin = plugin_cls()
                result = plugin.format(result, options)
    if newline_at_eof is True:
        if not result.endswith('\n'):
            result += '\n'
    elif newline_at_eof is False:
        result = result.rstrip('\n')
    return result


def split(sql, encoding=None, dialect=None, strip_semicolon=False):
    """Split *sql* into single statements.

    :param sql: A string containing one or more SQL statements.
    :param encoding: The encoding of the statement (optional).
    :param strip_semicolon: If True, remove trainling semicolons
        (default: False).
    :returns: A list of strings.
    """
    stack = engine.FilterStack(dialect=dialect, strip_semicolon=strip_semicolon)
    return [str(stmt).strip() for stmt in stack.run(sql, encoding)]
