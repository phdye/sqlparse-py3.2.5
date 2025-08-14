#
# Copyright (C) 2009-2020 the sqlparse authors and contributors
# <see AUTHORS file>
#
# This module is part of python-sqlparse and is released under
# the BSD License: https://opensource.org/licenses/BSD-3-Clause

"""Parse SQL statements."""

# Verbosity level for sqlparse, 0 by default. Higher values increase output.
verbosity = 0

import sys

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
__all__ = ['engine', 'filters', 'formatter', 'sql', 'tokens', 'cli', 'config', 'plugins', 'verbosity',
           'get_config']

# Mapping from option section names to plugin registry names.
_OPTION_TO_PLUGIN = {
    'lists': 'lists',
    'spacing': 'spacing_casing',
    'keywords': 'spacing_casing',
    'identifiers': 'spacing_casing',
    'dialect_options': 'dialect_strictness',
    'layout': 'dialect_strictness',
    'clauses': 'clauses',
    'joins': 'joins',
    'predicates': 'predicates',
    'case_expr': 'case_expr',
    'cte': 'cte',
    'subqueries': 'subqueries',
    'blocks': 'blocks',
    'declarations': 'blocks',
    'create_table': 'create_table',
    'comments': 'comments',
    'penalties': 'penalties',
}

# Mapping from plugin registry names to module names when they differ.
_PLUGIN_MODULES = {
    'lists': 'list_controls',
}


def get_config(path=None, cfg_path=None, style=None, include_defaults=True, **options):
    if path and verbosity >= 1:
        sys.stderr.write('[INFO] path = {0}\n'.format(path))
    if cfg_path is None:
        if verbosity >= 1:
            sys.stderr.write('[INFO] Located configuration from {0}\n'.format(cfg_path))
        cfg_path = config.find_config(path)
    if verbosity >= 1:
        sys.stderr.write('[INFO] Seeding with default configuration\n')
    cfg = config.DEFAULT_CONFIG.copy()
    if cfg_path:
        if verbosity >= 1:
            sys.stderr.write('[INFO] Loaded configuration from {0}\n'.format(cfg_path))
        cfg.update(config.load_config(cfg_path=cfg_path, include_defaults=False))
    try:
        style_opts = config.load_style(style)
    except ValueError:
        raise
    if verbosity >= 1:
        if style:
            if style.startswith('{') and style.endswith('}'):
                sys.stderr.write('[INFO] Loaded style from inline definition\n')
            else:
                sys.stderr.write('[INFO] Loaded style {0}\n'.format(style))
        else:
            sys.stderr.write('[INFO] No style specified\n')
    cfg.update(style_opts)
    if options:
        cfg.update(options)
        if verbosity >= 1:
            sys.stderr.write('[INFO] Loaded command line options\n')
    if not include_defaults:
        cfg = {k: v for k, v in cfg.items()
               if k not in config.DEFAULT_CONFIG or v != config.DEFAULT_CONFIG[k]}
    return cfg


def parse(sql, encoding=None, dialect=None, **kwargs):
    """Parse sql and return a list of statements.

    :param sql: A string containing one or more SQL statements.
    :param encoding: The encoding of the statement (optional).
    :returns: A tuple of :class:`~sqlparse.sql.Statement` instances.
    """
    if dialect is None:
        dialect = get_config(**kwargs).get('dialect')
    return tuple(parsestream(sql, encoding, dialect, **kwargs))


def parsestream(stream, encoding=None, dialect=None, **kwargs):
    """Parses sql statements from file-like object.

    :param stream: A file-like object.
    :param encoding: The encoding of the stream contents (optional).
    :returns: A generator of :class:`~sqlparse.sql.Statement` instances.
    """
    if dialect is None:
        dialect = get_config(**kwargs).get('dialect')
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
    # print('*** sqlparse.format', file=sys.stderr)
    path = options.pop('path', None)
    cfg_path = options.pop('cfg_path', None)
    style = options.pop('style', None)
    options = get_config(path=path, cfg_path=cfg_path, style=style, include_defaults=False, **options)
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
            plugin_name = _OPTION_TO_PLUGIN.get(name)
            if plugin_name is None:
                continue
            if plugins.get_plugin(plugin_name) is None:
                module = _PLUGIN_MODULES.get(plugin_name, plugin_name)
                try:
                    __import__('sqlparse.plugins.{0}'.format(module), {}, {}, ['*'])
                except Exception:
                    pass
            if plugins.get_plugin(plugin_name):
                if plugin_name == 'dialect_strictness':
                    options['dialect_strictness'] = True
                    continue
                if plugin_name == 'spacing_casing' and name == 'keywords':
                    if plugin_name not in plugin_sections:
                        plugin_sections[plugin_name] = {}
                    plugin_sections[plugin_name][name] = section
                    continue
                options.pop(name)
                if plugin_name in ('lists', 'subqueries'):
                    plugin_sections[plugin_name] = section
                elif plugin_name == name:
                    plugin_sections[plugin_name] = {name: section}
                else:
                    if plugin_name not in plugin_sections:
                        plugin_sections[plugin_name] = {}
                    plugin_sections[plugin_name][name] = section

    stack = engine.FilterStack(dialect=dialect)
    options = formatter.validate_options(options)
    options['dialect'] = dialect
    stack = formatter.build_filter_stack(stack, options)
    stack.postprocess.append(
        filters.SerializerUnicode(
            strip_trailing_whitespace=options.get('strip_trailing_whitespace', True)))
    result = ''.join(stack.run(sql, encoding))

    run_options = options.copy()

    for name, section in plugin_sections.items():
        plugin_opts = run_options.copy()
        plugin_opts.update(section)
        plugin_cls = plugins.get_plugin(name)
        if plugin_cls is not None:
            plugin = plugin_cls()
            result = plugin.format(result, plugin_opts)

    if newline_at_eof is True:
        if not result.endswith('\n'):
            result += '\n'
    elif newline_at_eof is False:
        result = result.rstrip('\n')
    return result


def split(sql, encoding=None, dialect=None, strip_semicolon=False, **kwargs):
    """Split *sql* into single statements.

    :param sql: A string containing one or more SQL statements.
    :param encoding: The encoding of the statement (optional).
    :param strip_semicolon: If True, remove trainling semicolons
        (default: False).
    :returns: A list of strings.
    """
    if dialect is None:
        dialect = get_config(**kwargs).get('dialect')
    stack = engine.FilterStack(dialect=dialect, strip_semicolon=strip_semicolon)
    return [str(stmt).strip() for stmt in stack.run(sql, encoding)]
