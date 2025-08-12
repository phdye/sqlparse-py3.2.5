import sqlparse
from sqlparse import config

def test_format_applies_clang_config(tmpdir):
    cfg = tmpdir.join('.sqlparse')
    cfg.write(
        'version: 1\n'
        'dialect:\n  mode: postgres\n'
        'layout:\n  newline_at_eof: true\n'
        'spacing:\n  space_around_operators: true\n'
        'keywords:\n  case: upper\n'
        'identifiers:\n  case: lower\n'
    )
    opts = config.load_config(str(tmpdir))
    formatted = sqlparse.format('perform Foo+1', **opts)
    assert formatted == 'PERFORM foo + 1\n'
