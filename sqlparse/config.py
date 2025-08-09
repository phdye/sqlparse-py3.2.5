"""Configuration file support for sqlparse."""

import os

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

# Default style options in internal (snake_case) names
DEFAULT_CONFIG = {
    'keyword_case': None,
    'identifier_case': None,
    'output_format': None,
    'strip_comments': False,
    'reindent': False,
    'indent_width': 2,
    'indent_after_first': False,
    'indent_columns': False,
    'reindent_aligned': False,
    'use_space_around_operators': False,
    'wrap_after': 0,
    'comma_first': False,
    'compact': False,
    'indent_tabs': False,
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
    'WrapAfter': 'wrap_after',
    'CommaFirst': 'comma_first',
    'Compact': 'compact',
    'IndentTabs': 'indent_tabs',
    'StripWhitespace': 'strip_whitespace',
    'TruncateStrings': 'truncate_strings',
    'TruncateChar': 'truncate_char',
    'RightMargin': 'right_margin',
    'BasedOnStyle': 'BasedOnStyle',
}

BOOL_TRUE = ['true', 'yes', 'on']
BOOL_FALSE = ['false', 'no', 'off']


def _parse_simple_yaml(text):
    """Parse a very small subset of YAML into a dict."""
    data = {}
    text = text.strip()
    if text.startswith('{') and text.endswith('}'):
        text = text[1:-1]
        lines = text.split(',')
    else:
        lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line in ('---', '...'):
            continue
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
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
        data[key] = value
    return data


def _parse_yaml(text):
    if yaml is not None:
        try:
            loaded = yaml.safe_load(text)
            if isinstance(loaded, dict):
                return loaded
            return {}
        except Exception:
            return {}
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
    if path:
        cfg_path = find_config(path)
        if cfg_path:
            cfg.update(load_from_file(cfg_path))
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

