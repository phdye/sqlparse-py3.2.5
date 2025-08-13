import os

import os
import sqlparse
from sqlparse import config


def test_load_style():
    style = config.load_style('postgres')
    assert style['keyword_case'] == 'lower'


def test_load_config(tmpdir):
    cfg_dir = tmpdir.mkdir('cfg')
    cfg_file = cfg_dir.join('.sqlparse')
    cfg_file.write('version: 1\nkeywords:\n  case: upper\n')
    options = config.load_config(str(cfg_dir))
    assert options['keyword_case'] == 'upper'


def test_load_config_file(tmpdir):
    cfg = tmpdir.join('style.yaml')
    cfg.write('version: 1\nkeywords:\n  case: lower\n')
    options = config.load_config(None, str(cfg))
    assert options['keyword_case'] == 'lower'


def test_load_config_ignores_comments(tmpdir, monkeypatch):
    monkeypatch.setattr(config, 'yaml', None)
    cfg_dir = tmpdir.mkdir('cfg_comment')
    cfg_file = cfg_dir.join('.sqlparse')
    cfg_file.write('version: 1\nkeywords:\n  case: upper   # comment\n')
    options = config.load_config(str(cfg_dir))
    assert options['keyword_case'] == 'upper'


def test_load_config_home_fallback(tmpdir, monkeypatch):
    home = tmpdir.mkdir('home')
    cfg = home.join('.sqlparse')
    cfg.write('version: 1\nkeywords:\n  case: lower\n')
    monkeypatch.setenv('HOME', str(home))
    options = config.load_config(str(tmpdir))
    assert options['keyword_case'] == 'lower'


def test_dump_config():
    opts = config.DEFAULT_CONFIG.copy()
    opts['keyword_case'] = 'upper'
    dumped = config.dump_config(opts)
    assert 'KeywordCase: upper' in dumped


def test_load_clang_config(tmpdir):
    cfg = tmpdir.join('style.yaml')
    cfg.write('version: 1\nlayout:\n  indent_width: 3\nkeywords:\n  case: lower\n')
    opts = config.load_clang_config(str(cfg))
    assert opts['indent_width'] == 3
    assert opts['keyword_case'] == 'lower'


def test_load_clang_config_newline_at_eof(tmpdir):
    cfg = tmpdir.join('newline.yaml')
    cfg.write('version: 1\nlayout:\n  newline_at_eof: true\n')
    opts = config.load_clang_config(str(cfg))
    assert opts['newline_at_eof'] is True


def test_load_config_preserve(tmpdir):
    cfg_dir = tmpdir.mkdir('cfg_preserve')
    cfg_file = cfg_dir.join('.sqlparse')
    cfg_file.write('version: 1\nkeywords:\n  case: preserve\nidentifiers:\n  case: preserve\n')
    options = config.load_config(str(cfg_dir))
    assert options['keyword_case'] == 'preserve'
    assert options['identifier_case'] == 'preserve'


def test_load_clang_config_preserve(tmpdir):
    cfg = tmpdir.join('style_preserve.yaml')
    cfg.write('version: 1\nkeywords:\n  case: preserve\nidentifiers:\n  case: preserve\n')
    opts = config.load_clang_config(str(cfg))
    assert opts['keyword_case'] == 'preserve'
    assert opts['identifier_case'] == 'preserve'


def test_load_clang_config_equals(tmpdir):
    cfg = tmpdir.join('style.ini')
    cfg.write('[sqlformat]\nversion = 1\nreindent = true\nkeyword_case = upper\n')
    opts = config.load_clang_config(str(cfg))
    assert opts['reindent'] is True
    assert opts['keyword_case'] == 'upper'


def test_load_clang_config_full_sections(tmpdir):
    cfg = tmpdir.join('style_full.yaml')
    cfg.write(
        'version: 1\n'
        'layout:\n'
        '  indent_width: 4\n'
        '  use_tab: always\n'
        'spacing:\n'
        '  spaces_in_parens: true\n'
        'keywords:\n'
        '  case: upper\n'
        '  reserved_only: true\n'
        'identifiers:\n'
        '  case: lower\n'
        '  quote_style: single\n'
        'lists:\n'
        '  bin_pack: true\n'
        'clauses:\n'
        '  break:\n'
        '    select: before\n'
        'joins:\n'
        '  join_on_new_line: true\n'
        'predicates:\n'
        '  layout: compact\n'
        'case_expr:\n'
        '  indent_when_then: false\n'
        'cte:\n'
        '  one_per_line: false\n'
        'subqueries:\n'
        '  open_paren_same_line: false\n'
        'blocks:\n'
        '  begin_same_line: false\n'
        'declarations:\n'
        '  one_per_line: true\n'
        'create_table:\n'
        '  align_columns: false\n'
        'comments:\n'
        '  reflow_block_comments: true\n'
        '  keep_trailing_line_comment_with_code: false\n'
        '  pragma_freeze_directives: true\n'
        '  preserve_comment_position: true\n'
        'penalties:\n'
        '  over_column_limit: 500\n'
    )
    opts = config.load_clang_config(str(cfg))
    assert opts['indent_width'] == 4
    assert opts['indent_tabs'] is True
    assert opts['spaces_in_parens'] is True
    assert opts['keyword_case'] == 'upper'
    assert opts['keywords']['reserved_only'] is True
    assert opts['identifier_case'] == 'lower'
    assert opts['identifiers']['quote_style'] == 'single'
    assert opts['lists']['bin_pack'] is True
    assert opts['clauses']['break']['select'] == 'before'
    assert opts['joins']['join_on_new_line'] is True
    assert opts['predicates']['layout'] == 'compact'
    assert opts['case_expr']['indent_when_then'] is False
    assert opts['cte']['one_per_line'] is False
    assert opts['subqueries']['open_paren_same_line'] is False
    assert opts['blocks']['begin_same_line'] is False
    assert opts['declarations']['one_per_line'] is True
    assert opts['create_table']['align_columns'] is False
    assert opts['comments']['reflow_block_comments'] is True
    assert opts['comments']['keep_trailing_line_comment_with_code'] is False
    assert opts['comments']['pragma_freeze_directives'] is True
    assert opts['comments']['preserve_comment_position'] is True
    assert opts['penalties']['over_column_limit'] == 500


def test_format_uses_config_file(tmpdir, monkeypatch):
    cfg = tmpdir.join('.sqlparse')
    cfg.write('version: 1\nkeywords:\n  case: upper\nidentifiers:\n  case: upper\n')
    monkeypatch.chdir(str(tmpdir))
    formatted = sqlparse.format('select foo')
    assert formatted.strip() == 'SELECT FOO'


def test_format_uses_cfg_path(tmpdir):
    cfg = tmpdir.join('style.yaml')
    cfg.write('version: 1\nkeywords:\n  case: upper\nidentifiers:\n  case: upper\n')
    formatted = sqlparse.format('select foo', cfg_path=str(cfg))
    assert formatted.strip() == 'SELECT FOO'
