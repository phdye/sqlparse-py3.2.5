#!/usr/bin/env python
#
# Copyright (C) 2009-2020 the sqlparse authors and contributors
# <see AUTHORS file>
#
# This module is part of python-sqlparse and is released under
# the BSD License: https://opensource.org/licenses/BSD-3-Clause

"""Module that contains the command line app.

Why does this file exist, and why not put this in __main__?
  You might be tempted to import things from __main__ later, but that will
  cause problems: the code will get executed twice:
  - When you run `python -m sqlparse` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``sqlparse.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``sqlparse.__main__`` in ``sys.modules``.
  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import argparse
import os
import sys
from io import TextIOWrapper

import sqlparse
from sqlparse import config as spconfig
from sqlparse.exceptions import SQLParseError


# TODO: Add CLI Tests
# TODO: Simplify formatter by using argparse `type` arguments
def create_parser():
    _CASE_CHOICES = ['upper', 'lower', 'capitalize', 'preserve']

    parser = argparse.ArgumentParser(
        prog='sqlformat',
        description='Format FILE according to OPTIONS. Use "-" as FILE '
                    'to read from stdin.',
        usage='%(prog)s  [OPTIONS] FILE, ...',
    )

    parser.add_argument('filename')

    parser.add_argument(
        '--style',
        dest='style',
        metavar='STYLE',
        help='Formatting style (name, "file", or inline YAML)')

    parser.add_argument(
        '--config',
        dest='config',
        metavar='FILE',
        help='Read formatting options from YAML FILE (default ".sqlparse")')

    parser.add_argument(
        '--dump-config',
        dest='dump_config',
        action='store_true',
        default=False,
        help='Dump configuration and exit')

    parser.add_argument(
        '-o', '--outfile',
        dest='outfile',
        metavar='FILE',
        help='write output to FILE (defaults to stdout)')

    parser.add_argument(
        '--version',
        action='version',
        version=sqlparse.__version__)

    group = parser.add_argument_group('Formatting Options')

    group.add_argument(
        '-k', '--keywords',
        metavar='CHOICE',
        dest='keyword_case',
        choices=_CASE_CHOICES,
        default=None,
        help='change case of keywords, CHOICE is one of {}'.format(
            ', '.join('"{}"'.format(x) for x in _CASE_CHOICES)))

    group.add_argument(
        '-i', '--identifiers',
        metavar='CHOICE',
        dest='identifier_case',
        choices=_CASE_CHOICES,
        default=None,
        help='change case of identifiers, CHOICE is one of {}'.format(
            ', '.join('"{}"'.format(x) for x in _CASE_CHOICES)))

    group.add_argument(
        '-l', '--language',
        metavar='LANG',
        dest='output_format',
        choices=['python', 'php'],
        default=None,
        help='output a snippet in programming language LANG, '
             'choices are "python", "php"')

    group.add_argument(
        '--strip-comments',
        dest='strip_comments',
        action='store_true',
        default=None,
        help='remove comments')

    group.add_argument(
        '-r', '--reindent',
        dest='reindent',
        action='store_true',
        default=None,
        help='reindent statements')

    group.add_argument(
        '--indent_width',
        dest='indent_width',
        default=None,
        type=int,
        help='indentation width (defaults to 2 spaces)')

    group.add_argument(
        '--indent_after_first',
        dest='indent_after_first',
        action='store_true',
        default=None,
        help='indent after first line of statement (e.g. SELECT)')

    group.add_argument(
        '--indent_columns',
        dest='indent_columns',
        action='store_true',
        default=None,
        help='indent all columns by indent_width instead of keyword length')

    group.add_argument(
        '-a', '--reindent_aligned',
        action='store_true',
        default=None,
        help='reindent statements to aligned format')

    group.add_argument(
        '-s', '--use_space_around_operators',
        action='store_true',
        default=None,
        help='place spaces around mathematical operators')

    group.add_argument(
        '--wrap_after',
        dest='wrap_after',
        default=None,
        type=int,
        help='Column after which lists should be wrapped')

    group.add_argument(
        '--comma_first',
        dest='comma_first',
        default=None,
        type=bool,
        help='Insert linebreak before comma (default False)')

    group.add_argument(
        '--compact',
        dest='compact',
        default=None,
        type=bool,
        help='Try to produce more compact output (default False)')

    group.add_argument(
        '--encoding',
        dest='encoding',
        default='utf-8',
        help='Specify the input encoding (default utf-8)')

    group.add_argument(
        '--dialect', '--flavor',
        dest='dialect',
        metavar='DIALECT',
        default=None,
        help='Specify SQL dialect (default flexible)')

    return parser


def _error(msg):
    """Print msg and optionally exit with return code exit_."""
    sys.stderr.write('[ERROR] {}\n'.format(msg))
    return 1


def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args)
    if args.filename == '-':
        cfg_path = os.getcwd()
    else:
        cfg_path = args.filename
    options = spconfig.DEFAULT_CONFIG.copy()
    cfg_file = args.config or spconfig.find_config(cfg_path)
    if cfg_file:
        try:
            options.update(spconfig.load_clang_config(cfg_file))
        except ValueError as e:
            return _error(str(e))
    try:
        options.update(spconfig.load_style(args.style))
    except ValueError as e:
        return _error(str(e))

    arg_dict = vars(args)
    for key in spconfig.DEFAULT_CONFIG.keys():
        if key in arg_dict and arg_dict[key] is not None:
            options[key] = arg_dict[key]

    if args.dump_config:
        sys.stdout.write(spconfig.dump_config(options))
        return 0

    if args.filename == '-':  # read from stdin
        wrapper = TextIOWrapper(sys.stdin.buffer, encoding=args.encoding)
        try:
            data = wrapper.read()
        finally:
            wrapper.detach()
    else:
        try:
            with open(args.filename, encoding=args.encoding) as f:
                data = ''.join(f.readlines())
        except (IOError, OSError) as e:
            return _error(
                'Failed to read {}: {}'.format(args.filename, e))

    close_stream = False
    if args.outfile:
        try:
            stream = open(args.outfile, 'w', encoding=args.encoding)
            close_stream = True
        except (IOError, OSError) as e:
            return _error('Failed to open {}: {}'.format(args.outfile, e))
    else:
        stream = sys.stdout

    try:
        formatter_opts = sqlparse.formatter.validate_options(options)
    except SQLParseError as e:
        return _error('Invalid options: {}'.format(e))

    s = sqlparse.format(data, **formatter_opts)
    stream.write(s)
    stream.flush()
    if close_stream:
        stream.close()
    return 0
