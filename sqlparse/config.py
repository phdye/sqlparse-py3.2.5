"""Configuration file support for sqlparse."""

import os

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

# Default style options in internal (snake_case) names
DEFAULT_CONFIG = {
    'dialect': 'default',
    'keyword_case': None,
    'identifier_case': None,
    'output_format': None,
    'strip_comments': False,
    'reindent': False,
    'indent_width': 2,
    'indent_after_first': False,
    'indent_columns': False,
    'reindent_aligned': False,
    'pad_after_keyword': 1,
    'align_longest_keyword': False,
    'id_layout': 'vertical',
    'initial_indent': 0,
    'initial_pad_after_keyword': None,
    'use_space_around_operators': False,
    'spaces_in_parens': False,
    'spaces_in_brackets': False,
    'space_before_call_paren': False,
    'wrap_after': 0,
    'comma_first': False,
    'compact': False,
    'indent_tabs': False,
    'newline_at_eof': None,
    'strip_whitespace': False,
    'truncate_strings': None,
    'truncate_char': '[...]',
    'right_margin': None,
}

# Predefined styles
PREDEFINED_STYLES = {
    'default': {},
    'postgres': {'keyword_case': 'lower'},
    'mysql': {'keyword_case': 'upper'},
}

# Mapping from config file keys to internal names
KEY_MAP = {
    'Dialect': 'dialect',
    'Flavor': 'dialect',
    'KeywordCase': 'keyword_case',
    'IdentifierCase': 'identifier_case',
    'OutputFormat': 'output_format',
    'StripComments': 'strip_comments',
    'Reindent': 'reindent',
    'IndentWidth': 'indent_width',
    'IndentAfterFirst': 'indent_after_first',
    'IndentColumns': 'indent_columns',
    'ReindentAligned': 'reindent_aligned',
    'UseSpaceAroundOperators': 'use_space_around_operators',
    'SpacesInParens': 'spaces_in_parens',
    'SpacesInBrackets': 'spaces_in_brackets',
    'SpaceBeforeCallParen': 'space_before_call_paren',
    'WrapAfter': 'wrap_after',
    'CommaFirst': 'comma_first',
    'Compact': 'compact',
    'IndentTabs': 'indent_tabs',
    'StripWhitespace': 'strip_whitespace',
    'TruncateStrings': 'truncate_strings',
    'TruncateChar': 'truncate_char',
    'RightMargin': 'right_margin',
    'PadAfterKeyword': 'pad_after_keyword',
    'AlignLongestKeyword': 'align_longest_keyword',
    'IdLayout': 'id_layout',
    'BasedOnStyle': 'BasedOnStyle',
}

BOOL_TRUE = ['true', 'yes', 'on']
BOOL_FALSE = ['false', 'no', 'off']


def _parse_simple_yaml(text):
    """Parse a small subset of YAML with limited nesting support."""
    data = {}
    stack = [data]
    indents = [0]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        if raw.strip() in ('---', '...'):
            continue
        indent = len(raw) - len(raw.lstrip(' '))
        line = raw.strip()
        if ':' in line:
            key, value = line.split(':', 1)
        elif '=' in line:
            key, value = line.split('=', 1)
        else:
            continue
        key = key.strip()
        value = value.strip()
        if value:
            value = value.split('#', 1)[0].rstrip()
        while indent < indents[-1]:
            stack.pop()
            indents.pop()
        if value == '':
            new_dict = {}
            stack[-1][key] = new_dict
            stack.append(new_dict)
            indents.append(indent + 2)
            continue
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        low = value.lower()
        if low in BOOL_TRUE:
            value = True
        elif low in BOOL_FALSE:
            value = False
        else:
            try:
                value = int(value)
            except Exception:
                pass
        stack[-1][key] = value
    return data


def _parse_yaml(text):
    if yaml is not None:
        try:
            loaded = yaml.safe_load(text)
            if isinstance(loaded, dict):
                return loaded
            return {}
        except Exception:
            return _parse_simple_yaml(text)
    return _parse_simple_yaml(text)


def load_from_file(path):
    """Load options from a configuration file."""
    try:
        stream = open(path, 'r')
        try:
            text = stream.read()
        finally:
            stream.close()
    except OSError:
        return {}
    data = _parse_yaml(text) or {}
    return _convert_keys(data)


def load_from_string(text):
    data = _parse_yaml(text) or {}
    return _convert_keys(data)


def _convert_keys(data):
    result = {}
    based = data.pop('BasedOnStyle', None)
    if based:
        base = PREDEFINED_STYLES.get(str(based).lower())
        if base is None:
            base = {}
        result.update(base)
    for key, value in data.items():
        mapped = KEY_MAP.get(key)
        if mapped and mapped != 'BasedOnStyle':
            if isinstance(value, str) and mapped in (
                    'keyword_case', 'identifier_case', 'output_format'):
                value = value.lower()
            result[mapped] = value
    return result


def load_clang_config(path):
    """Load options from a clang-style YAML configuration."""
    try:
        stream = open(path, 'r')
        try:
            text = stream.read()
        finally:
            stream.close()
    except OSError:
        return {}
    data = _parse_yaml(text) or {}
    version = data.get('version')
    if version != 1:
        raise ValueError('Unsupported config version: {0}'.format(version))

    opts = {}

    for key in DEFAULT_CONFIG:
        if key in data:
            val = data[key]
            if isinstance(val, str) and key in ('keyword_case', 'identifier_case', 'output_format'):
                val = val.lower()
            opts[key] = val

    # Dialect
    dialect = data.get('dialect')
    if isinstance(dialect, dict):
        mode = dialect.get('mode')
        if mode:
            opts['dialect'] = mode
        other = {k: v for k, v in dialect.items() if k != 'mode'}
        if other:
            opts['dialect_options'] = other

    # Layout options
    layout = data.get('layout')
    if isinstance(layout, dict):
        if 'indent_width' in layout:
            opts['indent_width'] = layout['indent_width']
        if 'column_limit' in layout:
            opts['wrap_after'] = layout['column_limit']
        if 'use_tab' in layout:
            use_tab = layout['use_tab']
            if isinstance(use_tab, str):
                use_tab = use_tab.lower() != 'never'
            opts['indent_tabs'] = bool(use_tab)
        if 'newline_at_eof' in layout:
            opts['newline_at_eof'] = layout['newline_at_eof']
        rem = {k: v for k, v in layout.items()
               if k not in ('indent_width', 'column_limit', 'use_tab', 'newline_at_eof')}
        if rem:
            opts['layout'] = rem

    # Spacing rules
    spacing = data.get('spacing')
    if isinstance(spacing, dict):
        if 'space_around_operators' in spacing:
            opts['use_space_around_operators'] = spacing['space_around_operators']
        if 'spaces_in_parens' in spacing:
            opts['spaces_in_parens'] = spacing['spaces_in_parens']
        if 'spaces_in_brackets' in spacing:
            opts['spaces_in_brackets'] = spacing['spaces_in_brackets']
        if 'space_before_call_paren' in spacing:
            opts['space_before_call_paren'] = spacing['space_before_call_paren']
        rem = {k: v for k, v in spacing.items() if k not in (
            'space_around_operators', 'spaces_in_parens',
            'spaces_in_brackets', 'space_before_call_paren')}
        if rem:
            opts['spacing'] = rem

    # Keyword casing
    keywords = data.get('keywords')
    if isinstance(keywords, dict):
        case = keywords.get('case')
        if case:
            opts['keyword_case'] = case.lower()
        rem = {k: v for k, v in keywords.items() if k != 'case'}
        if rem:
            opts['keywords'] = rem

    # Identifier casing
    identifiers = data.get('identifiers')
    if isinstance(identifiers, dict):
        case = identifiers.get('case')
        if case:
            opts['identifier_case'] = case.lower()
        rem = {k: v for k, v in identifiers.items() if k != 'case'}
        if rem:
            opts['identifiers'] = rem

    # Remaining top-level sections are stored verbatim so callers may
    # access the detailed formatting instructions defined in the config
    # file.  They currently don't map to built-in sqlparse options but
    # are preserved to allow external tools to consume them.
    for name in (
        'lists', 'clauses', 'joins', 'predicates', 'case_expr', 'cte',
        'subqueries', 'blocks', 'declarations', 'create_table',
        'comments', 'penalties',
    ):
        section = data.get(name)
        if isinstance(section, dict):
            opts[name] = section

    return opts


def find_config(start):
    """Search for a .sqlparse file starting from *start*."""
    if start is None:
        start = os.getcwd()
    if not os.path.isdir(start):
        start = os.path.dirname(start)
    current = os.path.abspath(start)
    while True:
        candidate = os.path.join(current, '.sqlparse')
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def load_config(path):
    cfg = DEFAULT_CONFIG.copy()
    cfg_path = find_config(path)
    if cfg_path:
        cfg.update(load_clang_config(cfg_path))
    return cfg


def load_style(style):
    if not style or style == 'file':
        return {}
    if style.startswith('{') and style.endswith('}'):
        return load_from_string(style)
    style_lower = style.lower()
    found = PREDEFINED_STYLES.get(style_lower)
    if found is None:
        raise ValueError('Unknown style: {0}'.format(style))
    return found.copy()


def dump_config(options):
    lines = []
    for key, snake in KEY_MAP.items():
        if snake == 'BasedOnStyle':
            continue
        if snake in options and options[snake] is not None:
            value = options[snake]
            if isinstance(value, bool):
                value = 'true' if value else 'false'
            lines.append('{0}: {1}'.format(key, value))
    return '\n'.join(lines) + '\n'

