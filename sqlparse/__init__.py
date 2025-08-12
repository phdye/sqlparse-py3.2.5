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

_PLUGIN_MODULES = {
    'lists': 'list_controls',
}


__version__ = '0.5.3'
__all__ = ['engine', 'filters', 'formatter', 'sql', 'tokens', 'cli', 'config']


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

    # Extract plugin specific sections.  "lists" requires a mapping to existing
    # formatter options before handing control over to the plugin.
    lists_opts = options.get('lists')
    if isinstance(lists_opts, dict):
        if 'wrap_after' in lists_opts and 'wrap_after' not in options:
            options['wrap_after'] = lists_opts['wrap_after']
        if 'leading_commas' in lists_opts and 'comma_first' not in options:
            options['comma_first'] = lists_opts['leading_commas']

    plugin_sections = {}
    for name in list(options.keys()):
        section = options.get(name)
        if isinstance(section, dict):
            if plugins.get_plugin(name) is None:
                module = _PLUGIN_MODULES.get(name, name)
                try:
                    __import__('sqlparse.plugins.{0}'.format(module), {}, {}, ['*'])
                except Exception:
                    pass
            if plugins.get_plugin(name):
                plugin_sections[name] = section
                options.pop(name)

    stack = engine.FilterStack(dialect=dialect)
    options = formatter.validate_options(options)
    stack = formatter.build_filter_stack(stack, options)
    stack.postprocess.append(filters.SerializerUnicode())
    result = ''.join(stack.run(sql, encoding))

    for name, plugin_opts in plugin_sections.items():
        plugin_cls = plugins.get_plugin(name)
        if plugin_cls is not None:
            result = plugin_cls().format(result, plugin_opts)
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
